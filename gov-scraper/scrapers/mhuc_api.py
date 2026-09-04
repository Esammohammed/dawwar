"""
Direct integration with the Ministry of Housing's own public JSON API
(api.mhuc.gov.eg) — discovered by watching network traffic with Playwright
against mhuc.gov.eg (a client-side-rendered SPA whose real `<a href>` links
don't exist statically, so GenericNewsScraper's HTML-link approach can't
reach it). The API itself needs no browser at all — plain httpx, verified
working directly. This is a better outcome than rendering the SPA: cleaner
structured data (real title, full HTML content, real ISO dates) straight
from the horse's mouth, since this is the Ministry's own official channel.

Endpoint: POST https://api.mhuc.gov.eg/api/PgPage/GetPagesByCategoryId
categoryId=25 is "بيانات صحفية" (press releases) — confirmed by inspecting
the live response; every sampled item was a ministry press release.
"""
from __future__ import annotations

import logging
from typing import AsyncGenerator, Dict, Any

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

API_URL = "https://api.mhuc.gov.eg/api/PgPage/GetPagesByCategoryId"
PRESS_RELEASE_CATEGORY_ID = 25
PAGE_SIZE = 20

# Must exactly match a seeded ScrapeSource.name in Django.
SOURCE_NAME = "وزارة الإسكان - بيانات صحفية (API)"


def _clean_html_to_text(html: str) -> str:
    """Strips the article's rich-text HTML content down to plain text —
    BeautifulSoup's get_text() naturally skips embedded base64 <img> data,
    it only walks text nodes."""
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


class MHUCApiScraper(BaseScraper):
    def __init__(self, seen_store):
        self._store = seen_store

    async def scrape(self, max_articles: int = 40) -> AsyncGenerator[Dict[str, Any], None]:
        fetched = 0
        page_number = 1

        async with httpx.AsyncClient() as client:
            while fetched < max_articles:
                payload = {
                    "categoryId": PRESS_RELEASE_CATEGORY_ID,
                    "isPaging": True,
                    "isSearch": False,
                    "langId": 1,
                    "pageNumber": page_number,
                    "pageSize": PAGE_SIZE,
                    "searchFilter": {"langId": 1, "term": "string"},
                }
                try:
                    resp = await client.post(API_URL, json=payload, timeout=20.0)
                    resp.raise_for_status()
                    data = resp.json()
                except (httpx.HTTPError, ValueError) as exc:
                    logger.warning("MHUC API request failed on page %d: %s", page_number, exc)
                    return

                items = data.get("data") or []
                if not items:
                    return  # no more pages

                for item in items:
                    if fetched >= max_articles:
                        return

                    unique_url = (item.get("uniqueUrl") or "").strip()
                    if not unique_url:
                        continue
                    # The API is inconsistent: most uniqueUrl values already
                    # use underscores (matching the site's real URL scheme,
                    # confirmed live), but some come back with literal spaces
                    # instead — which don't form a valid URL at all (verified:
                    # the space version fails to even connect, the
                    # underscore version resolves 200). Normalize to match.
                    unique_url = "_".join(unique_url.split())
                    source_url = f"https://mhuc.gov.eg/{unique_url}"

                    if self._store.is_seen(source_url):
                        continue

                    lngs = item.get("pgPageLngs") or [{}]
                    title = (lngs[0].get("title") or "").strip()
                    body = _clean_html_to_text(lngs[0].get("content") or "")
                    if not title or not body:
                        continue

                    self._store.add(source_url)
                    fetched += 1
                    yield {
                        "title": title,
                        "body": body,
                        "source_url": source_url,
                        "published_at": item.get("pageDate"),
                    }

                page_number += 1

        logger.info("%s: yielded %d new articles.", SOURCE_NAME, fetched)
