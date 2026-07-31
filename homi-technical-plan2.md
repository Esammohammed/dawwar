# Homi — Technical Plan v1

Stack: Django + DRF + Celery/Redis · PostgreSQL · React · AWS
Scope of this document: backend structure, database design, frontend structure, infrastructure, and a phased build order.

---

## 1. Architecture overview

A single Django project (modular monolith) exposing a REST API consumed by a React single-page app. Background work (scraping, notifications, booking expiry) runs in Celery workers sharing the same codebase. PostgreSQL is the single source of truth; Redis serves as cache and Celery broker; S3 + CloudFront store and serve all photos and documents.

```
React SPA (Arabic-first, RTL)
        │  HTTPS / JSON
        ▼
Django + DRF  ──────────────  Django Admin (your back office)
   │        │
   │        └── Celery workers ── gov-news scraper, booking expiry,
   │                              Telegram notifications
   ▼
PostgreSQL (source of truth)     Redis (cache + broker)     S3 (media)
```

Rule of thumb we agreed on: clean app boundaries now, service extraction later only when evidence demands it. The scraper is the first extraction candidate; Elasticsearch is the future search layer if Postgres filtering ever becomes the bottleneck.

---

## 2. Backend — Django project structure

```
homi/
├── config/                  # settings (base/dev/prod), urls, celery.py
├── apps/
│   ├── accounts/            # custom user, OTP auth, roles
│   ├── developers/          # developer companies + verification
│   ├── projects/            # government + developer projects
│   ├── govfeed/             # scraped announcements + sources
│   ├── listings/            # resale + developer units, media
│   ├── applications/        # gov application paperwork pipeline
│   └── engagement/          # inquiries, bookings
├── requirements/
└── manage.py
```

Every app keeps the standard shape: `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `tasks.py` (Celery), `tests/`.

### 2.1 accounts

Custom user model from day one (changing it later is painful). Phone is the primary identifier — your audience lives on phones and Telegram, not email.

- `User`: id (UUID), phone (unique, indexed), email (optional), full_name, role (`buyer` | `seller` | `staff` | `admin`), is_phone_verified, telegram_id (optional), created_at
- Auth: OTP over SMS (or WhatsApp) → JWT (djangorestframework-simplejwt). Password optional, added later for staff.

### 2.2 developers

- `Developer`: id, name, commercial_register_no, contact_phone, contact_email, logo, verified (bool), commission_terms (JSONField), notes, created_at
- Verification is manual through Django admin — you or your lawyer flips `verified` after checking papers.

### 2.3 projects

One model for both government and developer projects, discriminated by `type`.

- `Project`: id, type (`government` | `developer`), developer (FK, null for government), name, slug, governorate, city, district, description, status (`announced` | `open_for_booking` | `under_construction` | `delivered`), details (JSONField — delivery date, payment plans, amenities), cover_image, created_at
- Indexes: (type, status), (governorate, city), slug unique.

### 2.4 govfeed

The AI scraper writes here; nothing goes public without your approval.

- `ScrapeSource`: id, name, url, kind (`rss` | `html` | `api` | `facebook_page`), active, last_run_at
- `Announcement`: id, source (FK), project (FK, nullable — link after review), title, body, source_url, published_at, scraped_at, status (`pending_review` | `published` | `rejected`), ai_summary (text — Claude API-generated summary in Arabic)
- Celery beat schedule runs the scraper every N hours; a task de-duplicates by source_url hash.

### 2.5 listings — the core

One model for both features, discriminated by `type`.

- `Listing`: id, type (`resale` | `developer_unit`), project (FK, nullable for standalone resales), seller (FK User, null for developer units), developer (FK, null for resales), title, description,
  - unit facts: area_sqm, bedrooms, bathrooms, floor, finishing (`core_shell` | `semi` | `fully` | `lux`), unit_attributes (JSONField — view, garden, garage, etc.)
  - location: governorate, city, district (denormalized for filtering even when project is null)
  - money: asking_price, currency (default EGP), negotiable (bool)
  - resale/takeover fields (null for fresh units): original_price, amount_paid, transfer_fee, installment_plan (JSONField — remaining schedule)
  - workflow: status (`draft` | `under_review` | `active` | `reserved` | `sold` | `archived`), reviewed_by (FK staff), published_at, created_at
- `Media`: id, listing (FK), file (S3), kind (`photo` | `video` | `floorplan`), sort_order
- Indexes: (status, governorate, city), (status, asking_price), (status, bedrooms), (type, status), GIN index on unit_attributes if you filter on it later.
- Constraint: a check that resale listings have a seller and developer_unit listings have a developer.

### 2.6 applications

Your existing paperwork service, systemized.

- `Application`: id, user (FK), project (FK — government), status (`collecting_docs` | `ready` | `submitted` | `accepted` | `rejected` | `refunded`), documents (JSONField — checklist with S3 keys), service_fee, paid (bool), submitted_at, notes, created_at
- Status changes trigger a Celery task → notify the applicant (SMS/Telegram).

### 2.7 engagement

- `Inquiry`: id, listing (FK), user (FK, nullable — allow guest inquiries with phone only), phone, message, status (`new` | `contacted` | `closed`), assigned_to (FK staff), created_at
- `Booking`: id, listing (FK), user (FK), deposit_amount, status (`pending_payment` | `confirmed` | `expired` | `cancelled`), expires_at, created_at
- Booking creation runs inside a transaction with `select_for_update()` on the listing row — two people can never reserve the same unit. A Celery beat task expires unpaid bookings and flips the listing back to `active`.

---

## 3. API surface (DRF)

Public (no auth):
- `GET /api/projects/` + `GET /api/projects/{slug}/` — filters: type, governorate, status
- `GET /api/announcements/` — published only
- `GET /api/listings/` — filters: type, governorate, city, price min/max, bedrooms, area, finishing, has_installments; ordering: price, date. Cursor pagination.
- `GET /api/listings/{id}/`
- `POST /api/inquiries/` — guest allowed (phone + message)

Authenticated (JWT):
- `POST /api/auth/otp/request/` · `POST /api/auth/otp/verify/` → tokens
- `POST /api/listings/` — seller submits a resale (lands in `under_review`)
- `GET /api/me/listings/` · `GET /api/me/applications/` · `GET /api/me/bookings/`
- `POST /api/applications/` · `POST /api/bookings/`

Staff-only endpoints are unnecessary at first — Django admin covers review/approval workflows. Add staff APIs only if the admin stops being enough.

Cross-cutting: throttling on OTP and inquiry endpoints (spam protection), drf-spectacular for OpenAPI docs, all list endpoints cached in Redis with short TTL and invalidated on publish.

---

## 4. Database notes

- PostgreSQL 16 on RDS. UUID primary keys everywhere.
- JSONB (JSONField) for genuinely variable data only: unit_attributes, installment_plan, documents, commission_terms, project details. Everything you filter or join on stays as real columns.
- Money as `DecimalField(max_digits=14, decimal_places=2)` — never floats.
- Soft-delete via status/archived flags; nothing is hard-deleted (audit trail matters in real estate disputes).
- Migrations via Django's built-in system; every schema change goes through code review even when working solo — read your own migration before applying to prod.
- Backups: RDS automated daily snapshots + 7-day point-in-time recovery from day one.

### 4.1 Full schema reference (DDL)

This is the target schema the Django models must produce. Use it to verify migrations — Django generates the actual DDL, but the result should match this. Types are PostgreSQL.

```sql
-- ============ accounts ============
CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone             VARCHAR(20) NOT NULL UNIQUE,
    email             VARCHAR(254),
    full_name         VARCHAR(150) NOT NULL,
    role              VARCHAR(10) NOT NULL DEFAULT 'buyer'
                      CHECK (role IN ('buyer','seller','staff','admin')),
    is_phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    telegram_id       VARCHAR(50),
    password          VARCHAR(128),          -- nullable; staff only at first
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_role ON users (role);

CREATE TABLE otp_codes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone       VARCHAR(20) NOT NULL,
    code_hash   VARCHAR(128) NOT NULL,       -- never store the raw code
    purpose     VARCHAR(20) NOT NULL DEFAULT 'login',
    expires_at  TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_otp_phone ON otp_codes (phone, expires_at);

-- ============ developers ============
CREATE TABLE developers (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                   VARCHAR(200) NOT NULL,
    commercial_register_no VARCHAR(50),
    contact_phone          VARCHAR(20) NOT NULL,
    contact_email          VARCHAR(254),
    logo                   VARCHAR(500),     -- S3 key
    verified               BOOLEAN NOT NULL DEFAULT FALSE,
    commission_terms       JSONB NOT NULL DEFAULT '{}',
    notes                  TEXT,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============ projects ============
CREATE TABLE projects (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type         VARCHAR(12) NOT NULL
                 CHECK (type IN ('government','developer')),
    developer_id UUID REFERENCES developers(id) ON DELETE PROTECT,
    name         VARCHAR(200) NOT NULL,
    slug         VARCHAR(220) NOT NULL UNIQUE,
    governorate  VARCHAR(60) NOT NULL,
    city         VARCHAR(80) NOT NULL,
    district     VARCHAR(80),
    description  TEXT,
    status       VARCHAR(20) NOT NULL DEFAULT 'announced'
                 CHECK (status IN ('announced','open_for_booking',
                                   'under_construction','delivered')),
    details      JSONB NOT NULL DEFAULT '{}',
    cover_image  VARCHAR(500),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_project_developer CHECK (
        (type = 'developer' AND developer_id IS NOT NULL) OR
        (type = 'government' AND developer_id IS NULL)
    )
);
CREATE INDEX idx_projects_type_status ON projects (type, status);
CREATE INDEX idx_projects_location    ON projects (governorate, city);

-- ============ govfeed ============
CREATE TABLE scrape_sources (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(120) NOT NULL,
    url         VARCHAR(500) NOT NULL,
    kind        VARCHAR(15) NOT NULL
                CHECK (kind IN ('rss','html','api','facebook_page')),
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at TIMESTAMPTZ
);

CREATE TABLE announcements (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id      UUID NOT NULL REFERENCES scrape_sources(id) ON DELETE PROTECT,
    project_id     UUID REFERENCES projects(id) ON DELETE SET NULL,
    title          VARCHAR(300) NOT NULL,
    body           TEXT NOT NULL,
    ai_summary     TEXT,
    source_url     VARCHAR(700) NOT NULL,
    source_url_hash CHAR(64) NOT NULL UNIQUE,   -- sha256, dedupe key
    status         VARCHAR(15) NOT NULL DEFAULT 'pending_review'
                   CHECK (status IN ('pending_review','published','rejected')),
    published_at   TIMESTAMPTZ,
    scraped_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ann_status_pub ON announcements (status, published_at DESC);

-- ============ listings ============
CREATE TABLE listings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            VARCHAR(15) NOT NULL
                    CHECK (type IN ('resale','developer_unit')),
    project_id      UUID REFERENCES projects(id) ON DELETE PROTECT,
    seller_id       UUID REFERENCES users(id) ON DELETE PROTECT,
    developer_id    UUID REFERENCES developers(id) ON DELETE PROTECT,
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    -- unit facts
    area_sqm        NUMERIC(7,2) NOT NULL,
    bedrooms        SMALLINT NOT NULL DEFAULT 0,
    bathrooms       SMALLINT NOT NULL DEFAULT 0,
    floor           SMALLINT,
    finishing       VARCHAR(12)
                    CHECK (finishing IN ('core_shell','semi','fully','lux')),
    unit_attributes JSONB NOT NULL DEFAULT '{}',
    -- location (denormalized for filtering)
    governorate     VARCHAR(60) NOT NULL,
    city            VARCHAR(80) NOT NULL,
    district        VARCHAR(80),
    -- money
    asking_price    NUMERIC(14,2) NOT NULL,
    currency        CHAR(3) NOT NULL DEFAULT 'EGP',
    negotiable      BOOLEAN NOT NULL DEFAULT TRUE,
    -- takeover / resale fields (NULL for fresh developer units)
    original_price   NUMERIC(14,2),
    amount_paid      NUMERIC(14,2),
    transfer_fee     NUMERIC(14,2),
    installment_plan JSONB,
    -- workflow
    status        VARCHAR(15) NOT NULL DEFAULT 'draft'
                  CHECK (status IN ('draft','under_review','active',
                                    'reserved','sold','archived')),
    reviewed_by   UUID REFERENCES users(id) ON DELETE SET NULL,
    published_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_listing_owner CHECK (
        (type = 'resale'         AND seller_id IS NOT NULL) OR
        (type = 'developer_unit' AND developer_id IS NOT NULL
                                 AND project_id IS NOT NULL)
    )
);
CREATE INDEX idx_listings_search   ON listings (status, governorate, city);
CREATE INDEX idx_listings_price    ON listings (status, asking_price);
CREATE INDEX idx_listings_bedrooms ON listings (status, bedrooms);
CREATE INDEX idx_listings_type     ON listings (type, status);
CREATE INDEX idx_listings_project  ON listings (project_id)
    WHERE project_id IS NOT NULL;

CREATE TABLE media (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    file       VARCHAR(500) NOT NULL,        -- S3 key
    kind       VARCHAR(10) NOT NULL DEFAULT 'photo'
               CHECK (kind IN ('photo','video','floorplan')),
    sort_order SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX idx_media_listing ON media (listing_id, sort_order);

-- ============ applications ============
CREATE TABLE applications (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE PROTECT,
    project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE PROTECT,
    status       VARCHAR(18) NOT NULL DEFAULT 'collecting_docs'
                 CHECK (status IN ('collecting_docs','ready','submitted',
                                   'accepted','rejected','refunded')),
    documents    JSONB NOT NULL DEFAULT '[]',  -- [{name, s3_key, uploaded_at}]
    service_fee  NUMERIC(10,2) NOT NULL DEFAULT 0,
    paid         BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMPTZ,
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_apps_user   ON applications (user_id, created_at DESC);
CREATE INDEX idx_apps_status ON applications (status);

-- ============ engagement ============
CREATE TABLE inquiries (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id  UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,  -- guests allowed
    phone       VARCHAR(20) NOT NULL,
    message     TEXT,
    status      VARCHAR(10) NOT NULL DEFAULT 'new'
                CHECK (status IN ('new','contacted','closed')),
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_inq_listing ON inquiries (listing_id, created_at DESC);
CREATE INDEX idx_inq_status  ON inquiries (status, created_at DESC);

CREATE TABLE bookings (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id     UUID NOT NULL REFERENCES listings(id) ON DELETE PROTECT,
    user_id        UUID NOT NULL REFERENCES users(id) ON DELETE PROTECT,
    deposit_amount NUMERIC(12,2) NOT NULL,
    status         VARCHAR(16) NOT NULL DEFAULT 'pending_payment'
                   CHECK (status IN ('pending_payment','confirmed',
                                     'expired','cancelled')),
    expires_at     TIMESTAMPTZ NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_book_listing ON bookings (listing_id, status);
-- only one live booking per listing at a time
CREATE UNIQUE INDEX uniq_active_booking ON bookings (listing_id)
    WHERE status IN ('pending_payment','confirmed');
```

### 4.2 Relationship summary

| Relationship | Cardinality | On delete |
|---|---|---|
| developers → projects | 1 : N | PROTECT |
| projects → listings | 1 : N (nullable) | PROTECT |
| projects → announcements | 1 : N (nullable) | SET NULL |
| users → listings (seller) | 1 : N | PROTECT |
| listings → media | 1 : N | CASCADE |
| listings → inquiries | 1 : N | CASCADE |
| listings → bookings | 1 : N | PROTECT |
| users → applications | 1 : N | PROTECT |
| projects → applications | 1 : N | PROTECT |
| users → bookings | 1 : N | PROTECT |

PROTECT everywhere money or legal history is involved — you can never accidentally delete a user and lose their booking record. CASCADE only for pure child data (photos, inquiry threads) that is meaningless without its parent.

### 4.3 Django mapping notes for implementation

- `ON DELETE PROTECT` → `models.PROTECT`; `SET NULL` → `models.SET_NULL, null=True`; `CASCADE` → `models.CASCADE`.
- CHECK constraints (`chk_listing_owner`, `chk_project_developer`) → `Meta.constraints` with `models.CheckConstraint(condition=Q(...))`.
- The partial unique index `uniq_active_booking` → `models.UniqueConstraint(fields=['listing'], condition=Q(status__in=['pending_payment','confirmed']), name='uniq_active_booking')`. This is the DB-level safety net; `select_for_update()` in the booking view is the first line of defense.
- `source_url_hash` is computed in `Announcement.save()` (sha256 of normalized URL) — the unique index makes scraper re-runs idempotent.
- Choices enums live in one `enums.py` per app (`models.TextChoices`) so serializers and frontend share exact values.
- Later additions that need no redesign: `saved_searches` (user alerts), `price_history` (append-only listing price changes), `group_purchases` (the shared-ownership feature, pending legal), PostGIS `location POINT` column if map search arrives.

---

## 5. Frontend — React structure

Arabic-first with full RTL. English optional later. This is the single most important frontend decision for your market.

Stack:
- Vite + React 18 + TypeScript
- React Router v6
- TanStack Query (server state — listings, projects) — no Redux needed
- Small Zustand store for UI state (auth session, filters drawer)
- Tailwind CSS with `dir="rtl"` support (logical properties: `ms-`, `me-`, `ps-`, `pe-`)
- react-hook-form + zod for forms
- i18n: react-i18next, Arabic default

```
src/
├── api/            # axios client, typed endpoints, query hooks
├── components/     # ListingCard, PriceTag, FilterBar, Gallery,
│                   # InstallmentBadge, StatusChip, OtpInput
├── pages/
│   ├── Home              # hero + featured listings + latest gov news
│   ├── Listings          # search page: filters + grid + pagination
│   ├── ListingDetail     # gallery, facts, installment breakdown,
│   │                     # inquiry form, WhatsApp/call buttons
│   ├── Projects          # gov + developer projects index
│   ├── ProjectDetail     # project info + its available units
│   ├── GovNews           # published announcements feed
│   ├── SellYourUnit      # multi-step resale submission wizard
│   ├── Account           # my listings / applications / bookings
│   └── Auth              # phone → OTP flow
├── stores/         # auth, ui
├── i18n/           # ar.json (primary), en.json
└── App.tsx
```

Market-specific details that matter:
- Every listing detail page gets a WhatsApp deep-link and tap-to-call button — most of your deals will close on the phone, not in a checkout flow.
- The resale wizard asks for takeover numbers in the seller's language: "How much have you paid so far?", "What is the transfer fee (تنازل)?" — the form builds the installment_plan JSON.
- Listing photos lazy-load through CloudFront with resized variants (thumbnail/card/full) generated on upload by a Celery task.
- SEO: since it is a SPA, add prerendering for listing/project pages later (or move to Next.js in a v2 if organic search becomes a growth channel — do not start there).

---

## 6. Infrastructure (AWS)

Start simple, one step above manual:
- One EC2 instance (t3.medium) running Docker Compose: web (gunicorn), worker (celery), beat, nginx. Or Elastic Beanstalk if you prefer managed.
- RDS PostgreSQL (db.t4g.small, single-AZ to start), Redis via ElastiCache (t4g.micro)
- S3 bucket for media + CloudFront distribution; S3 bucket for frontend static hosting + CloudFront
- Route53 DNS, ACM certificates
- GitHub Actions CI/CD: test → build image → deploy on push to main
- Sentry for error tracking, CloudWatch alarms on CPU/disk/5xx
- Environments: `staging` and `production` from day one (staging can be a cheap single container)

Scale path when needed (in order): bigger EC2 → move containers to ECS Fargate behind an ALB → RDS read replica → Elasticsearch for search. Each step is independent; none requires rewriting.

---

## 7. Build order

Phase 1 — foundation (weeks 1–2)
Django project scaffold, custom User + OTP auth, Docker Compose dev environment, CI pipeline, deploy empty app to staging. React scaffold with RTL + routing + auth flow.

Phase 2 — listings core (weeks 3–5)
Listing/Media models + admin review workflow, public listing API with filters, S3 uploads, resale submission wizard, listings search page + detail page. **This is the MVP — a browsable, filterable resale marketplace.**

Phase 3 — projects & developers (weeks 6–7)
Developer + Project models/admin, developer_unit listings, project pages linking to their units.

Phase 4 — gov feed (week 8)
ScrapeSource + Announcement models, first scraper task for 1–2 official sources, review-then-publish flow, GovNews page, auto-post approved announcements to your Telegram channel (this feeds your 20k audience back into the site).

Phase 5 — applications & bookings (weeks 9–10)
Application pipeline with document checklist, Booking with locking + expiry, account dashboard pages, SMS/Telegram notifications.

Phase 6 — polish & launch
Caching pass, SEO basics, analytics (Plausible or GA4), load test the listings endpoint, security review (throttling, permissions audit), production cutover.

Deferred by design: multi-site listing aggregator (legal review first), group-buying feature (needs legal structure), Elasticsearch, native apps.
