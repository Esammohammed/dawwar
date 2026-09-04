import logging
import asyncio
import json
from typing import AsyncGenerator, Dict, Any
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth

from .base import BaseScraper
from storage.seen_urls import SeenURLStore

logger = logging.getLogger(__name__)

BOT_DETECTION_PHRASES = ["confirm you are human", "human verification", "security check"]


class PropertyFinderScraper(BaseScraper):
    """
    Scrapes PropertyFinder.eg by extracting structured listing data
    directly from the Next.js __NEXT_DATA__ JSON embedded in the search
    results page. This avoids visiting individual detail pages (which are
    protected by Cloudflare Turnstile bot detection).
    """

    BASE_URL = "https://www.propertyfinder.eg"
    START_URL = "https://www.propertyfinder.eg/en/buy/properties-for-sale.html"

    def __init__(self, store: SeenURLStore):
        self.store = store
        self.stealth = Stealth()

    def _is_bot_blocked(self, soup: BeautifulSoup) -> bool:
        title = soup.title.string.lower() if soup.title and soup.title.string else ""
        return any(phrase in title for phrase in BOT_DETECTION_PHRASES)

    async def _wait_for_challenge(self, page: Page, max_wait: int = 60) -> bool:
        """Wait for bot challenge to clear (user may need to click manually)."""
        logger.warning("Bot challenge detected! Waiting up to %ds for it to clear...", max_wait)
        for _ in range(max_wait):
            await page.wait_for_timeout(1000)
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            if not self._is_bot_blocked(soup):
                logger.info("Challenge cleared!")
                return True
        logger.warning("Challenge did NOT clear after %ds.", max_wait)
        return False

    def _extract_listings_from_next_data(self, soup: BeautifulSoup) -> list[Dict[str, Any]]:
        """Parse the __NEXT_DATA__ script and pull structured listing data."""
        next_data_tag = soup.find("script", id="__NEXT_DATA__")
        if not next_data_tag or not next_data_tag.string:
            logger.warning("No __NEXT_DATA__ found on page")
            return []

        try:
            data = json.loads(next_data_tag.string)
            listings = (
                data.get("props", {})
                .get("pageProps", {})
                .get("searchResult", {})
                .get("listings", [])
            )
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error("Failed to parse __NEXT_DATA__: %s", e)
            return []

        results = []
        for entry in listings:
            prop = entry.get("property", {})
            if not prop:
                continue

            # Build the canonical detail URL
            details_path = prop.get("details_path", "")
            source_url = f"{self.BASE_URL}{details_path}" if details_path else prop.get("share_url", "")

            if not source_url or self.store.is_seen(source_url):
                continue

            # Price
            price_obj = prop.get("price", {})
            asking_price = price_obj.get("value", 0)
            currency = price_obj.get("currency", "EGP")

            # Location
            location = prop.get("location", {})
            full_address = location.get("full_name", "")

            # Images — grab medium-quality versions
            images = []
            for img in prop.get("images", []):
                url = img.get("medium") or img.get("small")
                if url:
                    images.append(url)

            # Agent / Broker info
            agent = prop.get("agent", {})
            broker = prop.get("broker", {})
            seller_name = agent.get("name", "") or broker.get("name", "")
            seller_phone = broker.get("phone", "")

            # Size
            size_obj = prop.get("size", {})
            area_sqm = size_obj.get("value", 0) if isinstance(size_obj, dict) else 0

            raw = {
                "source_site": "propertyfinder",
                "source_url": source_url,
                "title": prop.get("title", ""),
                "description": prop.get("description", ""),
                "raw_price": str(asking_price),
                "raw_address": full_address,
                "asking_price": asking_price,
                "currency": currency,
                "area_sqm": area_sqm,
                "bedrooms": prop.get("bedrooms", 0),
                "bathrooms": prop.get("bathrooms", 0),
                "property_type": prop.get("property_type", ""),
                "source_seller_name": seller_name,
                "source_seller_phone": seller_phone,
                "image_urls": images,
            }
            results.append(raw)

        return results

    async def scrape(self, max_pages: int = 5) -> AsyncGenerator[Dict[str, Any], None]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()
            await self.stealth.apply_stealth_async(page)

            try:
                for page_num in range(1, max_pages + 1):
                    url = f"{self.START_URL}?page={page_num}"
                    logger.info("Fetching PropertyFinder Page %d: %s", page_num, url)

                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(4000)

                    content = await page.content()
                    soup = BeautifulSoup(content, "html.parser")

                    # Handle bot challenge
                    if self._is_bot_blocked(soup):
                        cleared = await self._wait_for_challenge(page, max_wait=60)
                        if not cleared:
                            logger.error("Bot challenge not cleared. Stopping.")
                            break
                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")

                    # Extract all listings from the embedded JSON
                    raw_listings = self._extract_listings_from_next_data(soup)
                    logger.info(
                        "Page %d: extracted %d new listings from __NEXT_DATA__",
                        page_num,
                        len(raw_listings),
                    )

                    for raw in raw_listings:
                        logger.info(
                            "SCRAPED: title='%s', price=%s %s, images=%d, loc='%s'",
                            raw["title"][:60],
                            raw["asking_price"],
                            raw.get("currency", ""),
                            len(raw["image_urls"]),
                            raw["raw_address"],
                        )
                        self.store.add(raw["source_url"])
                        yield raw

                    # Polite delay between pages
                    await asyncio.sleep(3)
            finally:
                await browser.close()
