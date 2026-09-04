import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from main import ScraperPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_propertyfinder_job():
    logger.info("--- Starting Scheduled PropertyFinder Job ---")
    pipeline = ScraperPipeline()
    # Scrape first 50 pages every run (approx 1250 listings)
    await pipeline.run_propertyfinder(max_pages=50)
    logger.info("--- Finished Scheduled PropertyFinder Job ---")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    
    # Run every 6 hours
    scheduler.add_job(
        run_propertyfinder_job,
        trigger=IntervalTrigger(hours=6),
        id='propertyfinder_scraper',
        name='Scrape PropertyFinder',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started! Press Ctrl+C to exit.")
    
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == '__main__':
    start_scheduler()
