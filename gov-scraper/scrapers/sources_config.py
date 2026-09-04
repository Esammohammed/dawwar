"""
Per-source configuration for GenericNewsScraper.

`link_pattern` is the regex used to spot candidate article links on a
source's listing page. Two of these were verified against real, live HTML
while building this scraper (masrawy, dostor) — the rest are reasonable
best-effort patterns (mirroring how the two verified sources are actually
built — numeric-ID article paths are near-universal on Arabic news CMSs) but
**have not been confirmed against live markup** and should be spot-checked
before this scraper is relied on in production; see the module docstring in
generic_news_scraper.py for the fallback behavior when a pattern matches
nothing.

`keyword_hint` is only used as a cheap prefilter on anchor text at the
listing stage, to avoid fetching every single article on a general-news
homepage — the real program classification happens later in matcher.py
against the full article body.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class NewsSourceConfig:
    name: str  # must exactly match a seeded ScrapeSource.name in Django
    base_url: str
    listing_url: str
    link_pattern: str
    keyword_hint: List[str] = field(default_factory=lambda: [
        "سكن", "إسكان", "وحدات سكنية", "وزارة الإسكان", "حجز شقق", "عقار",
    ])


SOURCES = [
    NewsSourceConfig(
        name="مصراوي - أخبار العقارات",
        base_url="https://www.masrawy.com",
        # /news/realestate-news redirects/404s as of this writing — the
        # section/708/ path is the live one, verified while building this.
        listing_url="https://www.masrawy.com/news/realestate-news/section/708/",
        # Verified live: /news/<category>/details/<y>/<m>/<d>/<id>/<slug>
        link_pattern=r"https://www\.masrawy\.com/news/[\w_]+/details/\d{4}/\d{1,2}/\d{1,2}/\d+/[^\s\"'#]*",
    ),
    NewsSourceConfig(
        name="الدستور",
        base_url="https://www.dostor.org",
        listing_url="https://www.dostor.org",
        # Verified live: root-relative /<7-8 digit id>
        link_pattern=r"(?:https://www\.dostor\.org)?/\d{6,8}(?:$|(?=[\"'#?]))",
    ),
    NewsSourceConfig(
        name="عقار 24",
        base_url="https://aqaar24.com",
        listing_url="https://aqaar24.com",
        # Not live-verified — WordPress-style slug URLs assumed; tune before relying on this.
        link_pattern=r"https://aqaar24\.com/[\w\-%]+/?(?=[\"'#?]|$)",
    ),
    NewsSourceConfig(
        name="البلد نيوز",
        base_url="https://www.elbalad.news",
        listing_url="https://www.elbalad.news",
        # Not live-verified — numeric-ID pattern assumed by analogy to دستور; tune before relying on this.
        link_pattern=r"https://www\.elbalad\.news/\d{6,8}(?:$|(?=[\"'#?]))",
    ),
    NewsSourceConfig(
        name="بروبرتي فايندر - المدونة",
        base_url="https://www.propertyfinder.eg",
        listing_url="https://www.propertyfinder.eg/blog",
        # Not live-verified — blog-slug pattern assumed; tune before relying on this.
        link_pattern=r"https://www\.propertyfinder\.eg/blog/[\w\-%]+/?(?=[\"'#?]|$)",
        keyword_hint=["سكن", "إسكان", "وحدات سكنية", "وزارة الإسكان", "حجز شقق"],
    ),
    NewsSourceConfig(
        name="الهيئة العامة للاستعلامات",
        base_url="https://www.sis.gov.eg",
        listing_url="https://www.sis.gov.eg/ar/%D8%A7%D9%84%D9%85%D8%B1%D9%83%D8%B2-%D8%A7%D9%84%D8%A5%D8%B9%D9%84%D8%A7%D9%85%D9%8A/%D8%A7%D9%84%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1/",
        # Not live-verified — sis.gov.eg's URL scheme wasn't inspected; tune before relying on this.
        link_pattern=r"https://sis\.gov\.eg/ar/[^\s\"'#]+",
    ),
    NewsSourceConfig(
        name="هيئة المجتمعات العمرانية الجديدة",
        base_url="https://services.nuca.gov.eg",
        listing_url="https://services.nuca.gov.eg/ar/NewsList.aspx",
        # NOT live-verified at all — the site refused connections outright
        # from the dev environment this was built in (network-level
        # ECONNREFUSED, not an HTTP error), so this pattern is a guess built
        # only from a search-result URL shape (NewsItemViewer.aspx?NID=541).
        # This is the government body that actually runs land-tender
        # announcements ("طروحات الأراضي": بيت الوطن، أراضي المدن الجديدة)
        # — added specifically for that coverage — but treat this entry as
        # unverified until confirmed reachable and scraping correctly from
        # an environment that can actually connect to it.
        link_pattern=r"NewsItemViewer\.aspx\?NID=\d+",
        keyword_hint=["سكن", "إسكان", "أرض", "أراضي", "طرح", "قطع"],
    ),
]
