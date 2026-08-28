import logging
import asyncio
from typing import AsyncGenerator, Dict, Any
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, BrowserContext

from .base import BaseScraper
from storage.seen_urls import SeenURLStore

logger = logging.getLogger(__name__)

class DubizzleScraper(BaseScraper):
    BASE_URL = "https://www.dubizzle.com.eg"
    START_URL = "https://www.dubizzle.com.eg/en/properties/"

    def __init__(self, store: SeenURLStore):
        self.store = store

    async def scrape(self, max_pages: int = 5) -> AsyncGenerator[Dict[str, Any], None]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            try:
                for page_num in range(1, max_pages + 1):
                    url = f"{self.START_URL}?page={page_num}"
                    logger.info(f"Fetching Dubizzle Page {page_num}: {url}")
                    
                    page = await context.new_page()
                    await page.goto(url, wait_until="networkidle")
                    
                    # Extract listing URLs from the search results page
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Dubizzle listing cards usually have links containing /ad/
                    links = soup.select('a[href*="/ad/"]')
                    listing_urls = list(set([self.BASE_URL + link['href'] if link['href'].startswith('/') else link['href'] for link in links]))
                    
                    await page.close()
                    
                    for listing_url in listing_urls:
                        if self.store.is_seen(listing_url):
                            continue
                            
                        raw = await self._scrape_listing_detail(context, listing_url)
                        if raw:
                            self.store.add(listing_url)
                            yield raw
                            
                        # Small delay to avoid aggressive blocking
                        await asyncio.sleep(2)
            finally:
                await browser.close()

    async def _scrape_listing_detail(self, context: BrowserContext, url: str) -> Dict[str, Any] | None:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            
            # Click "Show phone number" button
            phone = ""
            try:
                # The button usually contains text like "Show phone number" or has a specific class
                phone_btn = page.locator("button:has-text('Show phone number')")
                if await phone_btn.count() > 0:
                    await phone_btn.first.click()
                    # Wait for phone number to appear in the DOM
                    await page.wait_for_timeout(1000)
                    
                    # Re-parse page content after click
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Try to extract the phone number which usually appears in an anchor with href="tel:..."
                    tel_links = soup.select('a[href^="tel:"]')
                    if tel_links:
                        phone = tel_links[0]['href'].replace('tel:', '').strip()
            except Exception as e:
                logger.warning(f"Could not click phone number on {url}: {e}")

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Basic Extraction (OpenAI will normalize this later)
            title_elem = soup.find('h1')
            title = title_elem.text.strip() if title_elem else ''
            
            desc_elem = soup.find('div', {'data-aut-id': 'itemDescriptionContent'})
            description = desc_elem.text.strip() if desc_elem else ''
            
            price_elem = soup.find('span', {'data-aut-id': 'itemPrice'})
            raw_price = price_elem.text.strip() if price_elem else ''
            
            location_elem = soup.find('span', {'data-aut-id': 'itemLocation'})
            raw_location = location_elem.text.strip() if location_elem else ''

            # Image extraction (from the gallery)
            image_urls = []
            img_tags = soup.select('picture img')
            for img in img_tags:
                src = img.get('src')
                if src and 'http' in src:
                    image_urls.append(src)
            image_urls = list(set(image_urls))

            return {
                "source_site": "dubizzle",
                "source_url": url,
                "title": title,
                "description": description,
                "raw_price": raw_price,
                "raw_address": raw_location,
                "source_seller_phone": phone,
                "source_seller_name": "", # Often hidden on Dubizzle
                "image_urls": image_urls
            }
        except Exception as e:
            logger.error(f"Failed to scrape detail {url}: {e}")
            return None
        finally:
            await page.close()
