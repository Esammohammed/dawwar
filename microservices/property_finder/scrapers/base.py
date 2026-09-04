from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any

class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, max_pages: int = 10) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Yields raw listing dictionaries. 
        The dictionary should contain at least:
        - title
        - description
        - raw_price
        - raw_location
        - image_urls (list of strings)
        - source_url
        - source_site
        - source_seller_name
        - source_seller_phone
        """
        pass
        yield {}
