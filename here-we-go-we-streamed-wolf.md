# Verified Contract-Exit Marketplace ("Safe Exit") — Feature Plan

## Context

AqarExit (aqarexit.com) runs a specialized resale product on top of the normal
Egyptian installment-property market: an owner who is struggling with (or just
wants out of) their developer installment contract can transfer it to a new
buyer at their **original contract price**, recovering exactly what they paid
in cash — no markup for the seller, and the platform's 1.25% commission is
charged to the **buyer**, not the seller. Every listing on that page carries a
"document-verified" trust badge and shows the buyer's immediate gain vs.
today's market price. There's also a standalone "Safe Exit Calculator" that,
with no login required, compares cancelling a contract (developer penalty)
against transferring it (recovering full paid value) — this doubles as a lead
magnet.

The user wants Dawwar to offer this same "sell your unit if you can't keep up
with payments" product, and asked me to (a) extract AqarExit's actual feature
set by visiting the site, and (b) decide whether it should be a new
microservice or folded into the existing app, before any implementation.

This document is that plan.

---

## 1. What AqarExit actually offers (extracted from the live site)

**Business model**
- Seller recovers exactly the cash they've paid to date (contract price +
  paid installments) — no premium, enforced by an explicit "I understand I get
  paid back exactly what I paid, no more" checkbox.
- Buyer pays the platform's commission (1.25%); seller pays nothing.
- Every listing is "متحقق بالمستندات" (document-verified) — staff review the
  contract and payment receipts before a unit goes live.
- Owners only: AqarExit explicitly rejects/removes anything submitted by a
  broker or middleman — the whole pitch depends on the buyer paying the
  *original* contract price with no broker markup layered in.

**The `/opportunities` marketplace page**
- Search by project/area/unit code, sort options: newest, "best for me",
  featured, lowest cash required, lowest installment, biggest gain, closest
  to handover, ready-for-transfer.
- Filter: negotiable.
- Per-card data: cover photo, verified badge, ⭐ featured flag, developer +
  location, unit code, specs (type · rooms · baths · area), **cash required
  now** (المطلوب كاش دلوقتي = amount already paid + any transfer fee — *not*
  the full contract price), a green **"your gain vs. market"** box (today's
  developer price minus cash-required-now, net of the 1.25% commission), and
  **remaining owed to developer** (المتبقي للمطور).
- Site-wide stats bar: unit count, total market value.

**The "Safe Exit Calculator" (`/calculator`, no login)**
- Toggle: "I'm a buyer" / "I'm a unit owner".
- 3 inputs: total contract price, total paid to date, years over which it was
  paid.
- Output: a plain-numbers comparison of *cancel the contract* (developer
  forfeiture penalty) vs. *transfer it to a new buyer* (recover full paid
  value). Exact formula isn't published (proprietary/developer-specific) —
  results are explicitly labeled "استرشادية" (indicative only, not a
  substitute for reading your actual contract).
- No login/phone required to see a result — this is a deliberate lead magnet.

**The seller wizard (`/sellers`, 6 steps)**
- Confirmed **Step 1 — "بيانات الوحدة"**: developer name, project/compound
  name, total contract price, total paid to date, current developer price for
  the same unit today (optional — feeds the buyer-gain calculation), plus the
  no-markup acknowledgement checkbox.
- Site's published 5-stage process (not the same as the 6 form steps, but
  describes the end-to-end journey): evaluate contract for free → upload
  contract + payment receipts → team verifies and publishes a verified
  opportunity → platform matches a qualified buyer → supported transfer until
  payment lands.
- **Steps 2–6 of the wizard were not extractable** (site didn't render further
  without progressing through the form). I'm inferring reasonable step
  content below from Dawwar's existing data model and the 5-stage process
  description — flagged explicitly as my design, not scraped fact.

---

## 2. Architecture decision: extend the monolith, do not split into a microservice

**Decision: integrate as a new Django app (`apps.exit_deals`) inside the
existing backend, not a separate service.**

Why, concretely, based on what's actually in the codebase today
([backend/apps/listings/models.py](backend/apps/listings/models.py)):

- `Listing` already has `original_price`, `amount_paid`, `transfer_fee`,
  `installment_plan`, `negotiable`, `seller` — this feature reuses ~90% of an
  existing, working data model. A microservice would force either duplicating
  that model in a second database or making synchronous cross-service calls
  for every listing render — pure overhead for zero benefit today.
- Two existing patterns are direct templates for the two hardest parts of
  this feature:
  - `apps.engagement.Booking` — row-lock (`select_for_update`) + status flip +
    `expires_at` + a DB-level "only one active X per listing" constraint —
    exactly the shape needed if we ever add a matched-buyer lock step.
  - `apps.applications.Application` — a status-workflow model
    (`collecting_docs → ready → submitted → accepted/rejected`) with a
    `documents` field and staff review via Django admin, no dedicated
    moderation API — exactly the shape needed for exit-listing verification.
- The codebase is already a modular monolith (`apps/accounts`, `apps/listings`,
  `apps/developers`, `apps/projects`, `apps/applications`, `apps/engagement`,
  `apps/govfeed`) — one Postgres DB, one deploy, apps split by bounded
  context rather than by service. A new app is the idiomatic way to add a
  bounded feature here; a microservice would break the FK chain
  (`Listing.seller → User`, `Booking.listing → Listing`) that every other
  feature relies on, for a feature with no independent scaling, no separate
  team, and no polyglot requirement — none of the reasons that justify a
  service split are present.
- Splitting later is always possible once (if) this product needs independent
  scaling; doing it now is pure premature cost.

**What this means concretely:** one new Django app, one new set of frontend
routes/components, zero new docker-compose services, zero new infra.

**Decisions locked in with the user:**
- Feature name: **"تنازل بدون عمولة"** (Transfer, No Commission) — used in nav,
  page titles, and all new copy.
- The seller flow is a **brand-new wizard** at `/exit/sell` — the existing
  `SellYourUnit.jsx` / `/sell` form is left completely untouched.
- Verified exit listings get **both** a dedicated `/exit/opportunities` page
  **and** a badge/callout inside the main `/listings` marketplace — so
  `ListingCard.jsx` gets a small additive change (see §5).

---

## 3. Data model — `backend/apps/exit_deals` (new app)

Reuses the existing `Listing` model as-is (no changes to its fields) and adds
a thin extension, following the same "separate model referencing the core
entity" shape already used by `Booking`/`Inquiry`/`Application` rather than
bloating `Listing` with fields that only apply to this one sub-product.

**`ExitListing`** — `OneToOneField(Listing, related_name='exit_profile', on_delete=CASCADE)`
- `developer_current_price` — decimal, nullable. The one genuinely new number
  (AqarExit's "سعر نفس الوحدة من المطور النهارده"). Everything else AqarExit
  shows per-card is derivable from fields `Listing` already has:
  - **cash required now** = `listing.amount_paid + listing.transfer_fee`
  - **remaining to developer** = `listing.original_price - listing.amount_paid`
  - **buyer's gain vs. market** = `developer_current_price - cash_required_now`,
    net of `commission_rate`
- `owner_confirmed_no_markup` — bool, the wizard's acknowledgement checkbox.
- `verification_status` — choices `pending / verified / rejected`, default
  `pending`. Mirrors `ApplicationStatus`'s pattern. A listing must be
  `Listing.status == active` **and** `ExitListing.verification_status ==
  verified` to appear anywhere as a verified exit opportunity — this keeps
  the existing marketplace-visibility rule (`Listing.status`) orthogonal to
  the exit-specific trust badge.
- `verification_notes` — text, staff-only notes (rejection reason, broker
  suspicion, etc.), same role as `Application.notes`.
- `commission_payer` — choices `buyer / seller`, default `buyer`.
- `commission_rate` — decimal, defaulted from a new
  `settings.EXIT_DEFAULT_COMMISSION_RATE` (e.g. `1.25`) at creation time, so a
  later rate change doesn't retroactively alter already-published listings.
- `created_at`, `updated_at`.

> **Scope boundary:** `commission_payer`/`commission_rate` are informational
> display fields only. Nothing in this codebase collects payments today (even
> `Booking.deposit_amount` is just a DB figure, not a real charge) — actually
> billing the buyer's commission is out of scope for this plan.

**`ExitDocument`** — `FK(ExitListing, related_name='documents', on_delete=CASCADE)`
- `doc_type` — choices `contract / payment_receipt / other`.
- `file` — `FileField` (not `ImageField`, since contracts are frequently PDF
  scans), same disk-storage convention as `apps.listings.Media`.
- `uploaded_at`.
- Reuses/extends the existing `MediaUploadService` validation pattern
  ([backend/apps/listings/services.py](backend/apps/listings/services.py))
  as `ExitDocumentUploadService`, widening allowed MIME types to include
  `application/pdf`.

**`ExitLead`** — standalone, not linked to a `Listing` (captured *before* any
listing exists, from the calculator).
- `phone` (nullable — calculator results show without it; phone is only
  collected if the user opts into the follow-up CTA), `contract_price`,
  `amount_paid`, `years_paid`, `computed_result` (JSON snapshot of what was
  shown to them), `created_at`.
- Feeds staff follow-up via Django admin — this is the tool's actual
  lead-generation value, same as it clearly is on AqarExit.

No changes needed to `apps.accounts` — "owners only" is enforced the same way
AqarExit does it: staff reviewing the uploaded contract + payment receipts
against the listing's `seller`, via Django admin (see §4). No new KYC/ID-upload
infrastructure.

---

## 4. Backend — endpoints & admin

New app wiring: `apps.exit_deals` added to `INSTALLED_APPS`
([backend/config/settings.py](backend/config/settings.py)), new
`EXIT_DEFAULT_COMMISSION_RATE` setting, `include()`'d in
[backend/config/urls.py](backend/config/urls.py).

**Reused unchanged:** `POST /api/listings/` (base listing creation) and
`POST /api/listings/{id}/upload-media/` (property photos) — the exit wizard
calls these exact existing endpoints for steps 1 and 5 of its submission, no
duplication of listing-creation logic.

**New in `apps.exit_deals`:**
- `POST /api/exit-deals/listings/{listing_id}/profile/` — attaches
  `ExitListing` metadata to an already-created listing (must be owned by
  `request.user`), sets `verification_status=pending`.
- `POST /api/exit-deals/listings/{listing_id}/documents/` — multipart,
  repeatable, owner-only, via `ExitDocumentUploadService`.
- `GET /api/exit-deals/opportunities/` — read-only list/retrieve of verified
  exit listings (`ExitListing.verification_status=verified`,
  `listing__status=active`), supporting AqarExit-parity sort params: newest,
  lowest cash required, biggest gain, negotiable-only.
- `POST /api/exit-deals/calculator-leads/` — `AllowAny`, throttled, creates an
  `ExitLead`.
- `admin.py` — `ExitListingAdmin` (inline `ExitDocumentAdmin`, list filter on
  `verification_status`, bulk "mark verified / mark rejected" actions) and
  `ExitLeadAdmin`. This matches the existing codebase convention: regular
  `Listing.status` review already happens purely through Django admin with no
  dedicated moderation API — same here, no new surface area.

**Small, additive touch to `apps.listings`** (needed for the marketplace-badge
decision in §2): `ListingSerializer`
([backend/apps/listings/serializers.py](backend/apps/listings/serializers.py))
gets one new nullable `SerializerMethodField`, `exit_profile`, that returns
`None` for every ordinary listing and a small badge payload
(`cash_required_now`, `market_gain`, `remaining_to_developer`) only when a
verified `ExitListing` exists — lazily imported inside the method to avoid a
circular import with the new app. `ListingViewSet.get_queryset` gets
`.select_related('exit_profile')` added to avoid N+1 queries. Nothing else in
`apps.listings` changes.

---

## 5. Frontend

**New routes** (added to [frontend/src/App.jsx](frontend/src/App.jsx)):
- `/exit` — `pages/exit/ExitLanding.jsx`: the trust/value-prop page (mirrors
  AqarExit's `/sellers` intro): headline, the 4-point checklist extracted in
  §1 ("real contract review, not an estimate" / "documented cancel-vs-transfer
  comparison" / "honest recommendation, even if it's 'stay put'" / "free for
  sellers, buyer pays the 1.25%"), the "owners only, no brokers" callout, and
  two CTAs → Calculator and → Start Wizard.
- `/exit/calculator` — `pages/exit/ExitCalculator.jsx`: buyer/owner toggle, 3
  inputs (contract price, paid to date, years paid), instant client-side
  result via a new pure helper
  [frontend/src/utils/exitCalculator.js](frontend/src/utils/exitCalculator.js).
  Results render **without requiring login or phone** (matches the extracted
  UX); a soft-CTA below the result ("عايز نساعدك تخرج؟") optionally posts to
  `/api/exit-deals/calculator-leads/` only if the user opts in.
  The calculator's cancellation-vs-transfer math is clearly labeled
  "استرشادية" (indicative) with a configurable default penalty assumption —
  AqarExit's exact formula is proprietary/developer-specific and wasn't
  published, so this isn't presented as precise.
- `/exit/opportunities` — `pages/exit/ExitOpportunities.jsx`: same
  grid/filter shell as the existing `Listings.jsx`, pre-filtered to
  `is_verified_exit=true` against the new `/api/exit-deals/opportunities/`
  endpoint, with AqarExit-parity sort options (newest / lowest cash required /
  biggest gain / negotiable). **Reuses `ListingCard.jsx` directly** rather
  than forking a new card component, since that component already renders
  the exit badge/figures once `listing.exit_profile` is present (see below) —
  a direct payoff of choosing "badge in main marketplace" in §2.
- `/exit/sell` — `pages/exit/ExitSellWizard.jsx`, a new 6-step wizard,
  independent of `SellYourUnit.jsx`. Confirmed step 1 content from the live
  site; steps 2–6 are my inferred design (flagged, not scraped):
  1. Contract & unit financials — developer name, project/compound name,
     contract price, amount paid to date, developer's current price today
     (optional), + the no-markup acknowledgement checkbox. (Matches AqarExit's
     confirmed step 1 almost field-for-field.)
  2. Property specs & location — reuses the existing `GovernorateSelect`/
     `CitySelect` components already built for `SellYourUnit.jsx`.
  3. Owner confirmation — requires being logged in (existing phone-OTP auth);
     an explicit "أنا مالك الوحدة، مش وسيط أو سمسار" attestation checkbox.
  4. Documents — contract + payment-receipt upload, extending the existing
     `ImageUploadZone` pattern to also accept PDF.
  5. Property photos — reuses the existing `ImageUploadZone` and the
     unchanged `upload-media` endpoint.
  6. Review & submit.
  Submission chain mirrors `SellYourUnit.jsx`'s existing multi-request
  pattern: `POST /listings/` → `POST /exit-deals/listings/{id}/profile/` →
  `POST /exit-deals/listings/{id}/documents/` → `POST
  /listings/{id}/upload-media/`.

**Touched (additively) — the marketplace badge:**
- [frontend/src/components/ListingCard.jsx](frontend/src/components/ListingCard.jsx):
  when `listing.exit_profile` is present, render a "تنازل بدون عمولة" ribbon
  plus the cash-required-now figure and a green gain box — conditional
  addition, no change to existing rendering when it's absent (i.e. every
  current listing).
- [frontend/src/components/FilterBar.jsx](frontend/src/components/FilterBar.jsx):
  one new checkbox, "تنازل بدون عمولة فقط", following the exact pattern of
  the existing "Installments Only" checkbox, wired through
  [frontend/src/stores/filterStore.js](frontend/src/stores/filterStore.js)
  and passed as `is_verified_exit=true`.
- [frontend/src/components/Navbar.jsx](frontend/src/components/Navbar.jsx):
  one new nav link, "تنازل بدون عمولة" → `/exit`.
- [frontend/src/pages/SellYourUnit.jsx](frontend/src/pages/SellYourUnit.jsx):
  a small banner/link ("مش قادر تكمل أقساطك؟ اعرف تنازل بدون عمولة →")
  pointing to `/exit`, for discoverability from the existing sell flow. No
  logic changes to this file.
- `ar.js` / `en.js`: new `exitDeals` i18n namespace covering every string
  above.

---

## 6. Verification

1. `python manage.py makemigrations exit_deals && migrate` — confirm the
   `ExitListing` OneToOne, `ExitDocument`, `ExitLead` tables are created
   cleanly against the existing `listings` table with no FK issues.
2. Run backend + frontend dev servers (existing `docker-compose.yml` targets,
   unchanged).
3. Walk `/exit/sell` end-to-end as a logged-in test user: submit steps 1–6,
   confirm all four chained requests succeed and a `Listing` +
   `ExitListing(verification_status=pending)` + uploaded `ExitDocument`s +
   `Media` exist in the DB.
4. In Django admin, mark that `ExitListing` `verified` — confirm it now
   appears on `/exit/opportunities` and shows the badge/gain box on the card
   in the main `/listings` page, with `pending`/`rejected` ones confirmed
   absent from both.
5. Load `/exit/calculator` logged out, submit numbers, confirm a result
   renders with no auth call, and that the optional lead-capture CTA reaches
   `/api/exit-deals/calculator-leads/` only when explicitly submitted.
6. Confirm `SellYourUnit.jsx` and `Listings.jsx` behave exactly as before for
   ordinary (non-exit) listings — no regressions in the untouched paths.

