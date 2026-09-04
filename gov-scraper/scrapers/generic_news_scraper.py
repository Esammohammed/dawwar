"""
One scraper implementation, configured per source (see sources_config.py)
rather than six near-duplicate bespoke modules — the actually-reliable part
(pulling title/body from an article page's Open Graph meta tags, see
article_extractor.py) is identical across sources; what differs is only
"where do I find candidate article links", which is a two-line regex.
"""
from __future__ import annotations

import logging
import re
from typing import AsyncGenerator, Dict, Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper
from .article_extractor import extract_article
from .sources_config import NewsSourceConfig

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


class GenericNewsScraper(BaseScraper):
    def __init__(self, source: NewsSourceConfig, seen_store):
        self._source = source
        self._store = seen_store

    async def scrape(self, max_articles: int = 15) -> AsyncGenerator[Dict[str, Any], None]:
        pattern = re.compile(self._source.link_pattern)

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self._source.listing_url, headers=_HEADERS, timeout=20.0, follow_redirects=True)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("Failed to fetch listing page for %s: %s", self._source.name, exc)
                return

            soup = BeautifulSoup(resp.text, "html.parser")

            candidates: list[tuple[str, str]] = []  # (url, anchor_text)
            seen_urls_this_run: set[str] = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if not pattern.search(href):
                    continue
                full_url = urljoin(self._source.base_url, href)
                if full_url in seen_urls_this_run:
                    continue
                seen_urls_this_run.add(full_url)
                candidates.append((full_url, a.get_text(strip=True)))

            # Cheap prefilter on anchor text — purely an optimization to
            # skip fetching pages we're fairly confident aren't about
            # housing, since anchor text alone is too weak a signal to be
            # authoritative (most relevant articles don't repeat the exact
            # keyword_hint phrase in their link text). The REAL relevance
            # gate is matcher.is_housing_related(), run on the full fetched
            # title+body in main.py, before any GPT call or publish.
            #
            # Previously this had a `... or candidates` fallback that
            # scraped *everything* unfiltered whenever the anchor-text
            # filter matched zero candidates (the common case on a general
            # news homepage) — that was the actual bug that let Dubai
            # real-estate news, gold prices, and bank PR through to publish.
            # Removed: better to yield fewer candidates here and let
            # is_housing_related() be the sole authority than to silently
            # fall back to "everything."
            def looks_relevant(anchor_text: str) -> bool:
                if not anchor_text:
                    return True  # no text to judge — let it through, full-text check will filter
                return any(kw in anchor_text for kw in self._source.keyword_hint)

            filtered = [c for c in candidates if looks_relevant(c[1])]

            fetched = 0
            for url, _anchor_text in filtered:
                if fetched >= max_articles:
                    break
                if self._store.is_seen(url):
                    continue

                article = await extract_article(client, url)
                if not article:
                    continue

                self._store.add(url)
                fetched += 1
                yield article

        logger.info("%s: yielded %d new articles.", self._source.name, fetched)
