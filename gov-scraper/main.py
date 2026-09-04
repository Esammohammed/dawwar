import asyncio
import logging

from scrapers.generic_news_scraper import GenericNewsScraper
from scrapers.sources_config import SOURCES
from scrapers.mhuc_api import MHUCApiScraper, SOURCE_NAME as MHUC_SOURCE_NAME
from storage.seen_urls import SeenURLStore
from normalizer.openai_normalizer import OpenAINormalizer
from publisher.dawwar_client import DawwarClient
from matcher import match_project_slug, is_housing_related, names_plausibly_agree
from semantic_matcher import SemanticProgramMatcher
from config import MAX_ARTICLES_PER_SOURCE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GovScraperPipeline:
    def __init__(self):
        self.store = SeenURLStore()
        self.normalizer = OpenAINormalizer()
        self.client = DawwarClient()
        self.semantic_matcher = SemanticProgramMatcher()

    async def run(self, max_articles_per_source: int = MAX_ARTICLES_PER_SOURCE):
        # Loaded once per run, not per article — cheap (a handful of short
        # embeddings), and reused by every source below. No-ops in mock mode.
        await self.semantic_matcher.load_projects()

        total_published = 0
        total_skipped_irrelevant = 0
        total_suggested = 0

        # Each entry is (source_name, scraper_instance) — scraper_instance
        # just needs to implement BaseScraper.scrape(). Most sources go
        # through GenericNewsScraper (HTML link-pattern scraping); MHUC is
        # a direct JSON API integration instead (see scrapers/mhuc_api.py —
        # its site is a client-side-rendered SPA GenericNewsScraper can't
        # reach at all, but it turned out to have a clean public API
        # underneath once found).
        sources = [(cfg.name, GenericNewsScraper(cfg, self.store)) for cfg in SOURCES]
        sources.append((MHUC_SOURCE_NAME, MHUCApiScraper(self.store)))

        for source_name, scraper in sources:
            logger.info("Scraping %s ...", source_name)

            try:
                async for raw_article in scraper.scrape(max_articles=max_articles_per_source):
                    try:
                        title, body = raw_article["title"], raw_article["body"]

                        # The real relevance gate — runs on the full fetched
                        # title+body (not the weak anchor-text prefilter in
                        # generic_news_scraper.py). Skip before spending a
                        # GPT call or a publish attempt on anything that
                        # isn't plausibly Egyptian government housing news.
                        if not is_housing_related(title, body):
                            total_skipped_irrelevant += 1
                            logger.info("Skipping (not housing-related): %s", title[:60])
                            continue

                        # Layer 1 — deterministic (regex/literal), cheap, no
                        # drift risk. Tried first.
                        project_slug = match_project_slug(title, body)

                        # Layer 2 — semantic similarity against currently
                        # known programs, only if Layer 1 found nothing.
                        # Returns (slug, name) — the name is needed below to
                        # cross-check against what the article itself names.
                        semantic_candidate = None if project_slug else await self.semantic_matcher.match(title, body)

                        # Normalizer runs regardless — it's producing the
                        # summary/requirements either way. Layer 3's
                        # mentioned_program_name comes along for free in the
                        # same call, and doubles as the cross-check for
                        # Layer 2's candidate (see matcher.names_plausibly_agree
                        # for why Layer 2 alone isn't trustworthy enough).
                        normalized = await self.normalizer.normalize(raw_article)
                        mentioned_program_name = normalized.get("mentioned_program_name")

                        if semantic_candidate:
                            candidate_slug, candidate_name = semantic_candidate
                            if names_plausibly_agree(candidate_name, mentioned_program_name):
                                project_slug = candidate_slug
                            else:
                                logger.info(
                                    "Rejected semantic candidate %s — article names '%s', not '%s'",
                                    candidate_slug, mentioned_program_name, candidate_name,
                                )

                        # Layer 3 — only surfaced when Layers 1-2 found (and
                        # confirmed) nothing. Never auto-linked; a human
                        # confirms it in admin (see NeedsProgramReviewFilter)
                        # before it becomes a real Project.
                        suggested_program_name = None
                        if not project_slug:
                            suggested_program_name = mentioned_program_name
                            if suggested_program_name:
                                total_suggested += 1

                        announcement_id = await self.client.publish_announcement(
                            source_name=source_name,
                            project_slug=project_slug,
                            normalized=normalized,
                            source_url=raw_article["source_url"],
                            published_at=raw_article.get("published_at"),
                            suggested_program_name=suggested_program_name,
                        )
                        if announcement_id:
                            total_published += 1
                            logger.info(
                                "Published announcement %s (project=%s, suggested=%s): %s",
                                announcement_id, project_slug, suggested_program_name, normalized["title"][:60],
                            )
                    except Exception as exc:
                        logger.error("Pipeline error on %s: %s", raw_article.get("source_url"), exc)
            except Exception as exc:
                # One source being unreachable (SSL/DNS/timeout/site down)
                # must not stop the other independent sources from running —
                # this is exactly the kind of failure a scheduled scraper
                # hitting flaky external sites should expect routinely.
                logger.error("Source-level failure on %s, skipping: %s", source_name, exc)

        logger.info(
            "Run complete — %d published (%d with an AI-suggested unmatched program name), "
            "%d skipped as not housing-related.",
            total_published, total_suggested, total_skipped_irrelevant,
        )
        return total_published


# Entry point for testing directly: `python main.py`
if __name__ == "__main__":
    pipeline = GovScraperPipeline()
    asyncio.run(pipeline.run())
