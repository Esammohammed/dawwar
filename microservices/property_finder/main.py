import asyncio
import logging
from typing import Dict, Any

from scrapers.propertyfinder import PropertyFinderScraper
from storage.seen_urls import SeenURLStore
from normalizer.openai_normalizer import OpenAINormalizer
from downloader.image_downloader import ImageDownloader
from publisher.dawwar_client import DawwarClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import json

class ScraperPipeline:
    def __init__(self):
        self.store = SeenURLStore()
        self.normalizer = OpenAINormalizer()
        self.downloader = ImageDownloader()
        self.client = DawwarClient()

    async def run_propertyfinder(self, max_pages=1):
        scraper = PropertyFinderScraper(self.store)
        logger.info("Starting PropertyFinder scraper...")
        
        async for raw_listing in scraper.scrape(max_pages=max_pages):
            try:
                logger.info("--- NEW LISTING FOUND ---")
                logger.info(f"RAW IMAGE URLS FOUND: {raw_listing.get('image_urls')}")
                logger.debug(f"FULL RAW DATA: {json.dumps(raw_listing, indent=2, ensure_ascii=False)}")
                
                # 1. Normalize
                normalized = await self.normalizer.normalize(raw_listing)
                logger.info(f"NORMALIZED OUTPUT: {json.dumps(normalized, indent=2, ensure_ascii=False)}")
                
                # 2. Publish JSON
                listing_id = await self.client.publish_listing(normalized)
                logger.info(f"Published to Dawwar DB: {listing_id}")
                
                # 3. Download & Upload images
                image_urls = raw_listing.get('image_urls', [])
                if image_urls:
                    local_paths = await self.downloader.download_all(image_urls)
                    if local_paths:
                        await self.client.upload_media(listing_id, local_paths)
                        self.downloader.cleanup(local_paths)
                        logger.info(f"Uploaded {len(local_paths)} images for {listing_id}")
            except Exception as e:
                logger.error(f"Pipeline error on {raw_listing.get('source_url')}: {e}")

# Entry point for testing directly
if __name__ == "__main__":
    pipeline = ScraperPipeline()
    asyncio.run(pipeline.run_propertyfinder(max_pages=1))
