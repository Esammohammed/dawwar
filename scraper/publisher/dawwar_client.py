import httpx
import logging
from typing import Dict, Any, List
from pathlib import Path
from config import DAWWAR_API_URL, DAWWAR_BOT_TOKEN

logger = logging.getLogger(__name__)

class DawwarClient:
    def __init__(self):
        self.api_url = DAWWAR_API_URL
        self.headers = {
            "Authorization": f"Bearer {DAWWAR_BOT_TOKEN}",
            "Content-Type": "application/json"
        }

    async def publish_listing(self, data: Dict[str, Any]) -> str:
        """Publishes normalized JSON and returns the new Listing ID."""
        url = f"{self.api_url}/listings/scrape-import/"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=data, headers=self.headers, timeout=30.0)
            if resp.status_code != 201:
                logger.error(f"Failed to publish listing: {resp.text}")
                resp.raise_for_status()
            
            return resp.json()["id"]

    async def upload_media(self, listing_id: str, image_paths: List[Path]):
        """Uploads downloaded image files to the Dawwar API."""
        url = f"{self.api_url}/listings/{listing_id}/upload-media/"
        
        # httpx requires tuples of (filename, file_object, content_type)
        files_payload = []
        open_files = []
        
        try:
            for path in image_paths:
                f = open(path, 'rb')
                open_files.append(f)
                files_payload.append(
                    ('images', (path.name, f, 'image/jpeg'))
                )
            
            headers = {"Authorization": f"Bearer {DAWWAR_BOT_TOKEN}"}
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, files=files_payload, headers=headers, timeout=60.0)
                if resp.status_code != 201:
                    logger.error(f"Failed to upload media: {resp.text}")
                    resp.raise_for_status()
        finally:
            for f in open_files:
                f.close()
