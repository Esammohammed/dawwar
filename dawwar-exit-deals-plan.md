# "صفقة دوّار" — Verified Contract-Exit Listings — Feature Plan

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
set by visiting the site, and (b) decide how it should fit into the codebase,
before any implementation.

**This plan has been revised once already** (see §2) after building a first
version and finding the initial data-model split created real duplication —
that revision is captured below so the reasoning isn't lost.

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
- **Steps 2–6 of the wizard were not extractable.** Steps 2-6 in this plan
  (§5) are an inferred design based on Dawwar's existing data model and the
  5-stage process description — flagged explicitly as design, not scraped
  fact.

---

## 2. Architecture decision (revised): extend `apps.listings` directly — no separate app, no separate listing model

**Original decision** was a new `apps.exit_deals` Django app with its own
`ExitListing` (OneToOne → `Listing`) and `ExitDocument` models, reasoning that
exit-specific fields shouldn't pollute the shared `Listing`/`Media` models and
that this mirrored the `Booking`/`Application` pattern of separate models
referencing a core entity.

**That was implemented, then reconsidered** once the next real requirement
came up — exit listings need file uploads too (contract + payment receipts),
and building that turned out to just be reinventing `apps.listings.Media`
(FK to owner + `FileField` + a `kind` choice + `uploaded_at`) a second time
under a different name (`ExitDocument`). That duplication was the concrete
sign the split was wrong, and revisiting it further weakened the rest of the
original reasoning:

- `Listing` **already** carries nullable, type-specific columns —
  `original_price`, `amount_paid`, `transfer_fee`, `installment_plan` only
  mean something for resale listings and sit `NULL` for developer_unit/scraped
  ones. Adding a handful more nullable, exit-specific columns is the same
  pattern already in use on this exact model, not new pollution.
- The `Booking`/`Application` comparison was weaker than first presented:
  those are independent transactional entities with their own lifecycle (a
  booking can expire or be cancelled independent of the listing). Exit fields
  are just more facts about the *same* listing, not a separate process with
  its own lifecycle — closer to `original_price`/`amount_paid` than to
  `Booking`.
- A `Listing` row *is* the exit listing (same title, price, location, media,
  seller) — a `OneToOneField` split just adds a join and a second admin
  screen for data that's conceptually one record, which is exactly the
  fragmented admin UX that prompted this reconsideration in the first place.

**Revised decision:**
- Add exit-specific fields directly to `Listing`
  ([backend/apps/listings/models.py](backend/apps/listings/models.py)).
- Extend `Media`'s existing `MediaKind` choices to cover contract/receipt
  documents instead of a separate `ExitDocument` model — one upload pipeline
  for both property photos and legal documents, differentiated only by kind.
- Drop the `ExitListing` and `ExitDocument` models and the `apps.exit_deals`
  app entirely.
- The one thing that stays genuinely separate: **`ExitLead`** (calculator
  submissions) — these are captured *before* any listing exists and often
  never turn into one, so there's no `Listing` row to attach them to. This
  moves into `apps.engagement`, next to `Inquiry`/`Booking`, since that app is
  already the home for user-intent/lead-capture models.
- Net effect: **no new Django app at all.** This feature is now a handful of
  new fields + widened choices on two existing models, plus new frontend
  routes. Smaller footprint than either prior plan.

**Decisions locked in with the user (still standing):**
- Feature name — two-tier: **"صفقة دوّار"** (Safqet Dawwar) is the section
  brand (nav link, `/exit` page title/hero) — echoes the familiar idiom
  "صفقة العمر" (deal of a lifetime), leading with opportunity rather than
  distress, same framing AqarExit itself uses ("الفرص المتاحة" /
  opportunities). **"تنازل بدون عمولة"** (Transfer, No Commission) stays as
  the precise descriptive label on individual listing badges, the filter
  checkbox, and form copy.
- The seller flow is a **brand-new wizard** at `/exit/sell` — the existing
  `SellYourUnit.jsx` / `/sell` form is left untouched.
- Verified exit listings get **both** a dedicated `/exit/opportunities` page
  **and** a badge/callout inside the main `/listings` marketplace.

---

## 3. Data model — additions to `apps.listings` (+ one addition to `apps.engagement`)

**`Listing`** — new fields, all nullable/defaulted so every existing row and
every non-exit listing is unaffected:
- `is_exit_listing` — bool, default `False`. Gates all the fields below the
  same way `type` already gates `original_price`/`amount_paid`/etc. A new
  `CheckConstraint` mirrors the existing `chk_listing_owner` pattern:
  `is_exit_listing=True` requires `type=resale`.
- `developer_current_price` — decimal, nullable. The one genuinely new
  number (AqarExit's "سعر نفس الوحدة من المطور النهارده"). Everything else
  AqarExit shows per-card is derivable from fields `Listing` already has:
  - **cash required now** = `amount_paid + transfer_fee`
  - **remaining to developer** = `original_price - amount_paid`
  - **buyer's gain vs. market** = `developer_current_price - cash_required_now`,
    net of `exit_commission_rate`
- `owner_confirmed_no_markup` — bool, default `False`. The wizard's
  acknowledgement checkbox.
- `exit_verification_status` — choices `pending / verified / rejected`,
  default `pending`, nullable when `is_exit_listing=False`. A listing must be
  `status=active` **and** `exit_verification_status=verified` to appear
  anywhere as a verified exit opportunity — keeps the existing
  marketplace-visibility rule (`status`) orthogonal to the exit-specific
  trust badge.
- `exit_verification_notes` — text, staff-only (rejection reason, broker
  suspicion, etc.).
- `exit_commission_payer` — choices `buyer / seller`, default `buyer`.
- `exit_commission_rate` — decimal, defaulted from a new
  `settings.EXIT_DEFAULT_COMMISSION_RATE` (e.g. `1.25`) at creation time, so a
  later rate change doesn't retroactively alter already-published listings.

> **Scope boundary (unchanged):** `exit_commission_payer`/`exit_commission_rate`
> are informational display fields only. Nothing in this codebase collects
> payments today — actually billing the buyer's commission is out of scope.

**`Media`** — extend `MediaKind` choices:
- Add `contract`, `payment_receipt` alongside the existing `photo`, `video`,
  `floorplan`.
- `MediaUploadService`
  ([backend/apps/listings/services.py](backend/apps/listings/services.py))
  widens its MIME allowlist to accept `application/pdf` when `kind` is one of
  the two new document kinds (still images-only for `photo`/`floorplan`).
  Same model, same endpoint, same admin inline — no new upload pipeline.

**`ExitLead`** (moves into `apps.engagement`, alongside `Inquiry`/`Booking`) —
standalone, no `Listing` FK (captured before any listing exists):
- `phone` (nullable — calculator results show without it; only collected if
  the user opts into the follow-up CTA), `contract_price`, `amount_paid`,
  `years_paid`, `computed_result` (JSON snapshot of what was shown to them),
  `created_at`.
- Feeds staff follow-up via Django admin — this is the calculator's actual
  lead-generation value, same as it clearly is on AqarExit.

No changes needed to `apps.accounts` — "owners only" is enforced the same way
AqarExit does it: staff reviewing the uploaded contract + payment receipts
against the listing's `seller`, via Django admin. No new KYC/ID-upload
infrastructure.

**Migration note:** since `ExitListing`/`ExitDocument` already exist in the DB
from the first pass, the migration for this revision needs to (1) add the new
`exit_*` columns to `listings`, (2) backfill them from any existing
`ExitListing` rows, (3) migrate existing `ExitDocument` rows into `Media`
with the new kinds, (4) drop the `ExitListing`/`ExitDocument` tables and the
`apps.exit_deals` app once data is confirmed migrated.

---

## 4. Backend — endpoints & admin

No new app, no new `INSTALLED_APPS` entry, no new URL include beyond what
`apps.listings` and `apps.engagement` already have.

- `POST /api/listings/` — unchanged endpoint, now also accepts the new
  `is_exit_listing`, `developer_current_price`, `owner_confirmed_no_markup`
  fields in `ListingCreateSerializer`. Creating with `is_exit_listing=True`
  sets `exit_verification_status=pending` and stamps
  `exit_commission_rate` from settings.
- `POST /api/listings/{id}/upload-media/` — unchanged endpoint, now used for
  **both** property photos and exit documents; the existing `kind` param
  (already accepted per-file) just gains two more valid values.
- `GET /api/listings/exit-opportunities/` — new `@action` on the existing
  `ListingViewSet`, filtering `is_exit_listing=True,
  exit_verification_status=verified, status=active`, with AqarExit-parity
  sort params (newest / lowest cash required / biggest gain / negotiable).
  This is the endpoint backing `/exit/opportunities` on the frontend.
- `POST /api/engagement/exit-leads/` — new, lives with `Inquiry`/`Booking` in
  `apps.engagement`, `AllowAny`, throttled, creates an `ExitLead`.
- `ListingAdmin` ([backend/apps/listings/admin.py](backend/apps/listings/admin.py)):
  the new `exit_*` fields just appear on the same listing edit page (grouped
  in a fieldset), with a `list_filter` entry for `exit_verification_status`
  and bulk "mark exit-verified / mark exit-rejected" actions — no second
  admin section, no inline needed, since it's now all one model. This
  directly resolves the fragmented-admin complaint from earlier: one listing,
  one edit page, including its documents (via the existing `MediaInline`).
- `ExitLeadAdmin` registered in `apps.engagement`, next to `InquiryAdmin`.

**`ListingSerializer`** gets the new fields added directly (no lazy import,
no cross-app serializer composition needed anymore, since everything lives in
one model) — `is_exit_listing`, and (only when true) `cash_required_now`,
`market_gain`, `remaining_to_developer` as computed `SerializerMethodField`s
for the marketplace badge.

---

## 5. Frontend

**New routes** (added to [frontend/src/App.jsx](frontend/src/App.jsx)):
- `/exit` — `pages/exit/ExitLanding.jsx`, titled "صفقة دوّار": the
  trust/value-prop page (mirrors AqarExit's `/sellers` intro): headline, the
  4-point checklist from §1 ("real contract review, not an estimate" /
  "documented cancel-vs-transfer comparison" / "honest recommendation, even
  if it's 'stay put'" / "free for sellers, buyer pays the 1.25%"), the
  "owners only, no brokers" callout, two CTAs → Calculator and → Start
  Wizard.
- `/exit/calculator` — `pages/exit/ExitCalculator.jsx`: buyer/owner toggle, 3
  inputs (contract price, paid to date, years paid), instant client-side
  result via a new pure helper
  [frontend/src/utils/exitCalculator.js](frontend/src/utils/exitCalculator.js).
  Results render **without requiring login or phone**; a soft-CTA below the
  result ("عايز نساعدك تخرج؟") optionally posts to
  `/api/engagement/exit-leads/` only if the user opts in. Math is clearly
  labeled "استرشادية" (indicative) — AqarExit's exact formula is proprietary
  and wasn't published, so this isn't presented as precise.
- `/exit/opportunities` — `pages/exit/ExitOpportunities.jsx`: same
  grid/filter shell as `Listings.jsx`, hitting the new
  `GET /api/listings/exit-opportunities/` action, with AqarExit-parity sort
  options. **Reuses `ListingCard.jsx` directly** — it already renders the
  exit badge/figures once `listing.is_exit_listing` is present (below).
- `/exit/sell` — `pages/exit/ExitSellWizard.jsx`, new 6-step wizard,
  independent of `SellYourUnit.jsx`. Confirmed step 1 from the live site;
  steps 2–6 are inferred design:
  1. Contract & unit financials — developer name, project/compound name,
     contract price, amount paid to date, developer's current price today
     (optional), + the no-markup acknowledgement checkbox.
  2. Property specs & location — reuses existing `GovernorateSelect`/
     `CitySelect` components.
  3. Owner confirmation — requires login (existing phone-OTP auth); explicit
     "أنا مالك الوحدة، مش وسيط أو سمسار" attestation checkbox.
  4. Documents — contract + payment-receipt upload, extending the existing
     `ImageUploadZone` pattern to also accept PDF, tagged with the new
     `contract`/`payment_receipt` kinds.
  5. Property photos — reuses `ImageUploadZone` as-is.
  6. Review & submit.
  **Submission chain is now simpler than the first version:** `POST
  /listings/` (with `is_exit_listing=true` + financial fields in the same
  payload) → `POST /listings/{id}/upload-media/` (called twice: once for
  documents with `kind=contract`/`payment_receipt`, once for photos with
  `kind=photo`) — two endpoint calls instead of four, no new endpoints to
  build at all.

**Touched (additively) — the marketplace badge:**
- [frontend/src/components/ListingCard.jsx](frontend/src/components/ListingCard.jsx):
  when `listing.is_exit_listing` is true, render a "تنازل بدون عمولة" ribbon
  plus cash-required-now and a green gain box — conditional addition, no
  change when absent.
- [frontend/src/components/FilterBar.jsx](frontend/src/components/FilterBar.jsx):
  one new checkbox, "تنازل بدون عمولة فقط", same pattern as the existing
  "Installments Only" checkbox, wired through
  [frontend/src/stores/filterStore.js](frontend/src/stores/filterStore.js).
- [frontend/src/components/Navbar.jsx](frontend/src/components/Navbar.jsx):
  one new nav link, "صفقة دوّار" → `/exit`.
- [frontend/src/pages/SellYourUnit.jsx](frontend/src/pages/SellYourUnit.jsx):
  small banner/link ("مش قادر تكمل أقساطك؟ اعرف صفقة دوّار — تنازل بدون
  عمولة →") pointing to `/exit`. No logic changes to this file.
- `ar.js` / `en.js`: new `exitDeals` i18n namespace.

---

## 6. Verification

1. `python manage.py makemigrations listings engagement && migrate` — confirm
   the new `Listing`/`Media` columns/choices apply cleanly, and (per the
   migration note in §3) that existing `ExitListing`/`ExitDocument` data is
   backfilled before those tables are dropped.
2. Run backend + frontend dev servers (existing `docker-compose.yml`
   targets, unchanged).
3. Walk `/exit/sell` end-to-end as a logged-in test user: submit steps 1–6,
   confirm the two chained requests succeed and the `Listing` row has
   `is_exit_listing=True`, `exit_verification_status=pending`, and both
   document and photo `Media` rows attached.
4. In Django admin, mark that listing's `exit_verification_status=verified`
   on its single edit page — confirm it now appears on `/exit/opportunities`
   and shows the badge/gain box on the card in the main `/listings` page,
   with `pending`/`rejected` ones confirmed absent from both.
5. Load `/exit/calculator` logged out, submit numbers, confirm a result
   renders with no auth call, and the optional lead-capture CTA reaches
   `/api/engagement/exit-leads/` only when explicitly submitted.
6. Confirm `SellYourUnit.jsx` and `Listings.jsx` behave exactly as before for
   ordinary (non-exit) listings — no regressions in the untouched paths.
7. Confirm `apps.exit_deals` is fully removed (no leftover imports,
   `INSTALLED_APPS` entry, or URL includes) once the migration in step 1 is
   verified complete.

<!-- CHECKPOINT id="ckpt_mthqonqh_ik77ay" time="2026-08-31T21:17:23.369Z" note="auto" fixes=0 questions=0 highlights=0 sections="" -->

<!-- CHECKPOINT id="ckpt_mthrr8m2_u4s3ob" time="2026-08-31T21:47:23.354Z" note="auto" fixes=0 questions=0 highlights=0 sections="" -->

<!-- CHECKPOINT id="ckpt_mtkbbe18_z7uyvk" time="2026-09-02T16:30:28.556Z" note="auto" fixes=0 questions=0 highlights=0 sections="" -->
