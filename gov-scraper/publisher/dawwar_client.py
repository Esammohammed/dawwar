import logging
from typing import Any, Dict, Optional

import httpx

from config import DAWWAR_API_URL, DAWWAR_BOT_TOKEN

logger = logging.getLogger(__name__)


class DawwarClient:
    def __init__(self):
        self.api_url = DAWWAR_API_URL
        self.headers = {
            "Authorization": f"Bearer {DAWWAR_BOT_TOKEN}",
            "Content-Type": "application/json",
        }

    async def publish_announcement(
        self,
        source_name: str,
        project_slug: Optional[str],
        normalized: Dict[str, Any],
        source_url: str,
        published_at: Optional[str],
        suggested_program_name: Optional[str] = None,
    ) -> Optional[str]:
        """POSTs to /api/announcements/scrape-import/.

        Returns the new Announcement id, or None if the server rejected it
        (e.g. a duplicate source_url, or an unseeded source_name/project) —
        that's an expected outcome for a scraper polling the same pages
        repeatedly, not a crash-worthy error, so this logs and returns None
        rather than raising.
        """
        payload = {
            "source_name": source_name,
            "project_slug": project_slug,
            "title": normalized["title"],
            "body": normalized.get("body") or "",
            "ai_summary": normalized.get("ai_summary"),
            "requirements": normalized.get("requirements"),
            # Only ever set when project_slug is None (see main.py) — Layer
            # 3's AI suggestion, surfaced for a human to review in admin,
            # never auto-linked to a Project.
            "suggested_program_name": suggested_program_name,
            "source_url": source_url,
            "published_at": published_at,
        }
        url = f"{self.api_url}/announcements/scrape-import/"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
            if resp.status_code == 201:
                return resp.json()["id"]
            if resp.status_code == 400:
                logger.info("Skipped (expected — dedup/unseeded source): %s", resp.text)
                return None
            logger.error("Failed to publish announcement (%s): %s", resp.status_code, resp.text)
            resp.raise_for_status()
            return None
