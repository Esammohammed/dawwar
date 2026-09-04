# gov-scraper

Standalone microservice that scrapes Egyptian government-housing news
(سكن لكل المصريين 7/8, بيتك في مصر, منصة مصر العقارية, and general housing
ministry news) and publishes it into Dawwar's `Announcement` feed for staff
review. Sibling to the root `scraper/` (PropertyFinder/Dubizzle listings
scraper) — same overall shape (scrape → normalize with OpenAI → publish via
a bot-authenticated API call), different domain and a lighter dependency
footprint (no Playwright — these are plain HTML news sites, verified while
building this).

See `dawwar-govfeed-scraper-plan.md` at the repo root for the full design
rationale.

## How it works

1. **`scrapers/generic_news_scraper.py`** fetches each seeded source's
   listing page, finds candidate article links by regex
   (`scrapers/sources_config.py`), prefilters on anchor text, then fetches
   each candidate article and extracts `title`/`body` from its Open Graph
   meta tags (`scrapers/article_extractor.py` — this extraction approach was
   verified against real pages on masrawy.com and dostor.org; the other 4
   sources' link-pattern regexes are best-effort and should be spot-checked
   against live markup before relying on this in production).
2. **Which government program is this about?** — three layers, cheapest and
   most reliable first, each only tried if the one before found nothing:
   - **Layer 1 — `matcher.match_project_slug()`**, deterministic regex/
     literal matching. Handles numbered phases of "سكن لكل المصريين"
     generically (`سكن لكل المصريين\s*(\d+)` → `sakan-lel-masreyeen-{n}`),
     so a new phase 9, 10, ... matches immediately with no code change —
     phases 7/8 used to be hardcoded literal strings, which silently missed
     any other phase number. The matching backend endpoint auto-creates the
     `Project` row for a new phase on the fly (safe: both slug and name are
     mechanically derived from the number, never free-form AI text).
   - **Layer 2 — `semantic_matcher.py`**, cosine similarity between the
     article and whatever government `Project` rows *currently exist*
     (fetched live each run, not hardcoded) — catches name variants Layer 1
     doesn't anticipate. **Not trustworthy alone**: real testing found a
     fabricated program ("مبادرة سكني الجديد") scored 0.534 similarity
     against بيتك في مصر, squarely inside the same range genuine paraphrase
     matches score in (0.50-0.63) — no threshold on this signal alone can
     tell them apart, since both are just "government housing
     initiative"-shaped text.
   - **Layer 3 — folded into the normalizer prompt below, at no extra
     cost** — GPT is asked what specific program name (if any) the article
     literally states. This does double duty: it **validates Layer 2's
     candidate** (`matcher.names_plausibly_agree()` — reject the candidate
     if the article names something that doesn't overlap with it, which is
     exactly what catches the "سكني الجديد" false positive above), and if
     nothing matched at all, the name is stored as
     `Announcement.suggested_program_name` for a human to review in admin
     (`NeedsProgramReviewFilter`) — **never auto-linked**. This is the
     "semantic search, GPT-validated but not GPT-forced" design, chosen
     specifically to avoid letting an LLM freely classify (and potentially
     drift on) program assignment while still catching genuinely new/
     differently-named programs.
3. **`normalizer/openai_normalizer.py`** asks GPT-4o-mini for a cleaned
   title + 2-3 sentence Arabic summary + a `requirements` list **extracted
   only if the article explicitly states conditions/required papers** —
   the prompt is explicit that this must be `null`, not a guess, when the
   source text doesn't mention any — plus `mentioned_program_name` for
   Layer 3 above. Runs in a deterministic mock mode with no API key set,
   for testing without spending tokens (Layers 2-3 are simply skipped in
   mock mode, falling back to Layer 1 only).
4. **`publisher/dawwar_client.py`** POSTs the result to
   `POST /api/announcements/scrape-import/`, authenticated as the dedicated
   GovFeed bot user (see below). Lands as `status=pending_review` — nothing
   is ever auto-published; a human confirms via Django admin first.

## Setup

```bash
cp .env.example .env
pip install -r requirements.txt
```

Generate the bot token (run from `backend/`, with the Django env active):

```bash
python manage.py create_govfeed_bot
```

Paste the printed access token into `gov-scraper/.env` as `DAWWAR_BOT_TOKEN`.
Leave `OPENAI_API_KEY` blank to run in mock mode.

## Run

```bash
python main.py          # one-shot run against all seeded sources
python scheduler.py     # runs main.py's pipeline every 4 hours, forever
```

Or via Docker (also wired into the root `docker-compose.yml` as the
`gov_scraper` service):

```bash
docker compose up gov_scraper
```

## After a run

Scraped items land as `pending_review` — nothing is public until reviewed.
In Django admin (`/admin/govfeed/announcement/`), review and use the
**"Publish selected announcements"** bulk action.
