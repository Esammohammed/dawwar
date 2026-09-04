import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from main import GovScraperPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_govfeed_job():
    logger.info("--- Starting Scheduled GovFeed Scrape ---")
    pipeline = GovScraperPipeline()
    await pipeline.run()
    logger.info("--- Finished Scheduled GovFeed Scrape ---")


def start_scheduler():
    scheduler = AsyncIOScheduler()

    # Housing-program news moves far slower than real-estate listings
    # (the sibling scraper/ runs every 6h) — every 4h is plenty to catch new
    # announcements without hammering these sites. Matches the sibling's
    # behavior of also running once immediately on startup.
    scheduler.add_job(
        run_govfeed_job,
        trigger=IntervalTrigger(hours=4),
        id='govfeed_scraper',
        name='Scrape government housing news',
        replace_existing=True,
    )

    scheduler.start()
    logger.info("GovFeed scheduler started — running every 4 hours. Press Ctrl+C to exit.")

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    start_scheduler()
