"""
Layer 1 of the program matcher: deterministic (non-AI) matching. Kept
deterministic on purpose — see dawwar-govfeed-scraper-plan.md §5: trusting
an LLM to classify which program an article is about risks tagging drift
over time (the same program getting slightly different labels run to run),
where a fixed pattern against fixed, seeded Project slugs can't drift.

Two matchers live here:
- match_project_slug() — Layer 1. Regex for the one program family with
  numbered phases (سكن لكل المصريين N), so a new phase (9, 10, ...) matches
  immediately with no code change — this was a real limitation found in
  production use, where phases 7/8 were hardcoded as literal strings and a
  phase 9 announcement would have silently fallen through to the catch-all
  forever. Backed by a matching auto-create rule in
  apps.govfeed.serializers.AnnouncementScrapeImportSerializer.validate_project_slug
  — safe there for the same reason it's safe here: the slug and name are
  both mechanically derived from the captured number, never free-form text.
  Beitak Fi Masr / Masr El Aqareya Platform have no numbering, so they stay
  literal-phrase matches.
- is_housing_related() — the relevance gate (unchanged, further down).

Layer 2 (semantic similarity against whatever Project rows currently exist)
lives in semantic_matcher.py. Layer 3 (AI-suggested program name, surfaced
for human review, never auto-linked) is folded into the normalizer's
existing prompt (normalizer/openai_normalizer.py) — see main.py for how the
three layers are actually chained.

match_project_slug() returns None for anything that doesn't match a named
program — those still get scraped and published, just as the "مشاريع
الإسكان" general catch-all (project=None), unless a later layer finds
something.
"""
import re
from typing import Optional

_SAKAN_PHASE_RE = re.compile(r'سكن لكل المصريين\s*[-–:]?\s*(\d+|[٠-٩]+)')
_ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

LITERAL_PROGRAM_KEYWORDS: list[tuple[str, list[str]]] = [
    ("beitak-fi-masr", [
        "بيتك في مصر",
    ]),
    ("masr-el-aqareya-platform", [
        "منصة مصر العقارية", "منصه مصر العقاريه", "منصة مصر العقاريه",
    ]),
    # Added from real evidence, not guessed: after running the full pipeline
    # against ~300 real Ministry press releases, "حياة كريمة" came up 32
    # times and "بيت الوطن" 7 times as Layer-3 AI-suggested unmatched
    # program names — by far the strongest recurring signals.
    ("hayah-karima", [
        "حياة كريمة",
    ]),
    ("beit-el-watan", [
        "بيت الوطن",
    ]),
]


def match_project_slug(title: str, body: str) -> Optional[str]:
    """Return the seeded/derivable Project slug this article is about, or None."""
    haystack = f"{title}\n{body}"

    phase_match = _SAKAN_PHASE_RE.search(haystack)
    if phase_match:
        number = phase_match.group(1).translate(_ARABIC_DIGITS)
        return f"sakan-lel-masreyeen-{number}"

    for slug, keywords in LITERAL_PROGRAM_KEYWORDS:
        if any(kw in haystack for kw in keywords):
            return slug

    return None


_NAME_STOPWORDS = {'في', 'من', 'على', 'إلى', 'عن', 'مع', 'مبادرة', 'مشروع', 'برنامج'}


def names_plausibly_agree(reference_name: str, mentioned_name: Optional[str]) -> bool:
    """Cheap, rule-based cross-check for Layer 2's semantic candidate
    against Layer 3's mentioned_program_name (from the same normalizer
    call — no extra API cost). Real testing found Layer 2 alone isn't
    precise enough to trust on its own: a fictional program ("مبادرة سكني
    الجديد") scored 0.534 similarity against بيتك في مصر, squarely inside
    the range genuine paraphrase matches score in (0.50-0.63) — no
    similarity threshold can separate that case. Word-overlap against what
    the article *literally* names catches it.

    No mentioned_name at all means the article didn't clearly name a
    specific program itself — nothing to disagree with, so the semantic
    candidate is trusted as-is.
    """
    if not mentioned_name:
        return True
    ref_words = set(reference_name.split()) - _NAME_STOPWORDS
    mentioned_words = set(mentioned_name.split()) - _NAME_STOPWORDS
    if not ref_words or not mentioned_words:
        return True
    overlap = ref_words & mentioned_words
    return len(overlap) >= max(1, len(ref_words) // 2)


# Gates whether an article is government-housing content AT ALL, before it
# ever reaches the normalizer (GPT) or gets published — this is the fix for
# a real bug found in production use: generic_news_scraper.py's anchor-text
# prefilter has a fallback that scrapes *everything* unfiltered when nothing
# on a listing page matches, which was letting Dubai real-estate deals, gold
# prices, bank PR, and crime news through to publish. This is the actual
# authoritative filter — it runs against the full fetched title+body, not
# just weak anchor text.
#
# Deliberately built from specific multi-word phrases, not single generic
# words like "عقار"/"عقارات" (property/real-estate) — those match Dubai/UAE
# real-estate news just as easily as Egyptian government housing, which is
# exactly what leaked through. "وزارة الإسكان" (Ministry of Housing) alone
# is a strong enough signal since ministry activity is legitimately in scope
# as the "مشاريع الإسكان" catch-all — but a company whose *name* happens to
# contain "الإسكان" (e.g. بنك التعمير والإسكان) is not, on its own; that bank
# publishes plenty of unrelated commercial-banking PR.
HOUSING_RELEVANCE_KEYWORDS = [
    # The 4 named programs — always relevant regardless of anything else.
    "سكن لكل المصريين", "بيتك في مصر", "منصة مصر العقارية",
    # The ministry itself — its own activity is the general catch-all.
    "وزارة الإسكان", "وزيرة الإسكان", "وزير الإسكان",
    # Headline shorthand for the ministry ("الإسكان تستعرض...") — verb-led,
    # distinct from a company/bank NAME merely containing "الإسكان" (e.g.
    # بنك التعمير والإسكان), which is a noun phrase, not "الإسكان" as subject.
    "الإسكان تستعرض", "الإسكان تعلن", "الإسكان تطرح", "الإسكان تكشف",
    "الإسكان يعلن", "الإسكان يطرح", "الإسكان تتابع", "الإسكان تصدر",
    "الإسكان تفتتح",
    # Social/national housing schemes and terminology.
    "الإسكان الاجتماعي", "صندوق الإسكان الاجتماعي", "سكن مصر", "دار مصر",
    "بيت الوطن", "الإسكان المتميز",
    # Government tender/booking process vocabulary — specific to housing
    # ministry releases, not generic real-estate market coverage.
    "كراسة الشروط", "كراسة شروط", "حجز وحدات سكنية", "طرح وحدات سكنية",
    "وحدات سكنية جديدة", "التقديم على وحدات",
]


def is_housing_related(title: str, body: str) -> bool:
    """True only if the article is plausibly about Egyptian government
    housing — the gate before spending a GPT call or publishing anything."""
    haystack = f"{title}\n{body}"
    return any(kw in haystack for kw in HOUSING_RELEVANCE_KEYWORDS)
