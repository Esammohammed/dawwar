from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any


class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, max_articles: int = 15) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Yields raw article dictionaries, each containing at least:
        - title
        - body            (best-effort excerpt/description, not full article text)
        - source_url
        - published_at    (ISO string or None — not every source exposes this reliably)
        """
        pass
        yield {}
