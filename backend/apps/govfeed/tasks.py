import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def scrape_govfeed_task():
    """Deprecated — superseded by the gov-scraper microservice.

    This used to generate hardcoded mock Arabic announcements (no real HTTP
    fetch, no real AI summary) once an hour. Real scraping now happens in
    the standalone `gov-scraper/` service, which posts genuine announcements
    to POST /api/announcements/scrape-import/. Left as a harmless no-op
    (rather than deleted outright) in case anything still references this
    task name; it is no longer on CELERY_BEAT_SCHEDULE (see config/settings.py).
    """
    logger.info("scrape_govfeed_task is deprecated and no longer generates content — see gov-scraper/.")
    return "no-op: superseded by gov-scraper microservice"
