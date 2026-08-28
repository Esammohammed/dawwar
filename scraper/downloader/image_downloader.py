import httpx
import logging
import asyncio
import uuid
from pathlib import Path
from typing import List

from config import MEDIA_DIR

logger = logging.getLogger(__name__)

class ImageDownloader:
    def __init__(self, download_dir: str = MEDIA_DIR):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def _download_single(self, client: httpx.AsyncClient, url: str) -> Path | None:
        try:
            ext = url.split('?')[0].split('.')[-1]
            if len(ext) > 4: ext = 'jpg'
            
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = self.download_dir / filename
            
            response = await client.get(url, follow_redirects=True, timeout=15.0)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            return filepath
        except Exception as e:
            logger.warning(f"Failed to download image {url}: {e}")
            return None

    async def download_all(self, urls: List[str]) -> List[Path]:
        """Downloads a list of URLs and returns local Paths."""
        paths = []
        async with httpx.AsyncClient() as client:
            tasks = [self._download_single(client, url) for url in urls[:10]] # Limit to 10
            results = await asyncio.gather(*tasks)
            for res in results:
                if res: paths.append(res)
        return paths

    def cleanup(self, paths: List[Path]):
        """Deletes temp files after upload."""
        for path in paths:
            try:
                if path.exists():
                    path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete {path}: {e}")
