"""
Shared article-page extraction — verified against real pages on masrawy.com
and dostor.org while building this scraper: both reliably expose
`og:title`/`og:description` (via Open Graph meta tags, the standard nearly
every modern news CMS sets for social-sharing previews), so this is a much
more stable extraction target than guessing per-site body/container CSS
classes, which change with every redesign.

Falls back through `<meta name="description">` and finally the raw `<title>`
tag if Open Graph tags are missing on a given page.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def _meta_content(soup: BeautifulSoup, **attrs: str) -> Optional[str]:
    tag = soup.find("meta", attrs=attrs)
    return tag.get("content", "").strip() if tag and tag.get("content") else None


async def extract_article(client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
    """Fetch one article page and pull out title/body/published_at.

    Returns None (rather than raising) on fetch/parse failure so one bad
    link doesn't take down a whole scraping run — the caller just skips it.
    """
    try:
        resp = await client.get(url, headers=_HEADERS, timeout=20.0, follow_redirects=True)
        resp.raise_for_status()
    except (httpx.HTTPError, OSError) as exc:
        # OSError (not just httpx.HTTPError) is needed here — confirmed in
        # production use that some connection-level failures (SSL handshake
        # errors in particular) surface as raw ssl.SSLError/OSError rather
        # than being wrapped as an httpx exception, and previously slipped
        # past this except clause, killing the *rest* of this source's
        # batch (not just this one article) even though main.py's per-source
        # try/except stopped it from crashing the whole run.
        logger.warning("Failed to fetch article %s: %s", url, exc)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    title = (
        _meta_content(soup, property="og:title")
        or _meta_content(soup, attrs={"name": "twitter:title"})
        or (soup.title.string.strip() if soup.title and soup.title.string else None)
    )
    body = (
        _meta_content(soup, property="og:description")
        or _meta_content(soup, attrs={"name": "description"})
    )
    # Every site formats this differently (verified: Dostor uses US-style
    # "7/28/2026 5:46:18 PM", not ISO-8601, which Django's DRF rejects
    # outright) — normalize with dateutil rather than trust any one format,
    # and drop it entirely (None) rather than guess if parsing fails.
    # Announcement.published_at is nullable; scraped_at still records when
    # Dawwar found it either way.
    raw_published_at = _meta_content(soup, property="article:published_time")
    published_at = None
    if raw_published_at:
        try:
            published_at = date_parser.parse(raw_published_at).isoformat()
        except (ValueError, OverflowError):
            logger.info("Could not parse published_at '%s' for %s", raw_published_at, url)

    if not title or not body:
        # Both are needed downstream (the normalizer summarizes `body`) —
        # if a page genuinely has neither, it's not usable content.
        logger.info("Skipping %s — missing title/description meta tags.", url)
        return None

    return {
        "title": title,
        "body": body,
        "source_url": url,
        "published_at": published_at,
    }
