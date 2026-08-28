import httpx
import json
import logging
from bs4 import BeautifulSoup
from typing import AsyncGenerator, Dict, Any

from .base import BaseScraper
from storage.seen_urls import SeenURLStore

logger = logging.getLogger(__name__)

class PropertyFinderScraper(BaseScraper):
    BASE_URL = "https://www.propertyfinder.eg"
    START_URL = "https://www.propertyfinder.eg/en/buy/properties-for-sale.html"

    def __init__(self, store: SeenURLStore):
        self.store = store
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }

    async def fetch_phone(self, client: httpx.AsyncClient, agent_id: str) -> str:
        # e.g. agent_id: "george-mallak-30714"
        url = f"{self.BASE_URL}/en/agent/{agent_id}/phone/"
        try:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('data', {}).get('phone', '')
        except Exception:
            pass
        return ""

    async def scrape(self, max_pages: int = 10) -> AsyncGenerator[Dict[str, Any], None]:
        async with httpx.AsyncClient() as client:
            for page in range(1, max_pages + 1):
                url = f"{self.START_URL}?page={page}"
                logger.info(f"Fetching PropertyFinder Page {page}: {url}")
                
                try:
                    resp = await client.get(url, headers=self.headers)
                    resp.raise_for_status()
                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {e}")
                    break

                soup = BeautifulSoup(resp.text, 'html.parser')
                schema_tag = soup.find('script', id='serp-schema')
                
                if not schema_tag:
                    logger.warning("No JSON-LD schema found on page")
                    continue
                
                try:
                    schema_data = json.loads(schema_tag.string)
                except json.JSONDecodeError:
                    continue

                # Find the search results page schema
                results = None
                for graph_item in schema_data.get('@graph', []):
                    if '@type' in graph_item and 'SearchResultsPage' in graph_item['@type']:
                        results = graph_item.get('mainEntity', {}).get('itemListElement', [])
                        break
                        
                if not results:
                    break

                for item in results:
                    listing_url = item.get('url')
                    if not listing_url or self.store.is_seen(listing_url):
                        continue
                    
                    raw = await self._scrape_listing_detail(client, listing_url)
                    if raw:
                        self.store.add(listing_url)
                        yield raw

    async def _scrape_listing_detail(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any] | None:
        try:
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Get the structured schema from detail page
            schema_tag = None
            for script in soup.find_all('script', type='application/ld+json'):
                if 'RealEstateListing' in script.string:
                    schema_tag = script
                    break
                    
            if not schema_tag:
                return None
                
            schema = json.loads(schema_tag.string)
            if isinstance(schema, list):
                schema = schema[0]

            agent_url = schema.get('offers', {}).get('seller', {}).get('@id', '')
            agent_id = agent_url.split('/')[-1] if agent_url else ''
            
            phone = ""
            if agent_id:
                phone = await self.fetch_phone(client, agent_id)

            images = []
            img_objs = schema.get('image', [])
            if isinstance(img_objs, list):
                for img in img_objs:
                    if isinstance(img, dict):
                        images.append(img.get('url'))
                    elif isinstance(img, str):
                        images.append(img)
            elif isinstance(img_objs, dict):
                images.append(img_objs.get('url'))
            elif isinstance(img_objs, str):
                images.append(img_objs)

            # Some schemas bury the photos inside a 'photo' array
            if not images and 'photo' in schema:
                photo_objs = schema['photo']
                if isinstance(photo_objs, list):
                    for p in photo_objs:
                        if isinstance(p, dict):
                            images.append(p.get('image') or p.get('url'))
                        elif isinstance(p, str):
                            images.append(p)

            return {
                "source_site": "propertyfinder",
                "source_url": url,
                "title": schema.get('name', ''),
                "description": schema.get('description', ''),
                "raw_price": schema.get('offers', {}).get('price', 0),
                "raw_address": schema.get('address', {}),
                "area_sqm": schema.get('floorSize', {}).get('value'),
                "bedrooms": schema.get('numberOfBedrooms'),
                "bathrooms": schema.get('numberOfBathroomsTotal'),
                "amenities": [f.get('name') for f in schema.get('amenityFeature', [])],
                "source_seller_name": agent_url.split('/')[-1].replace('-', ' ').title() if agent_url else '',
                "source_seller_phone": phone,
                "image_urls": [img for img in images if img]
            }
        except Exception as e:
            logger.error(f"Failed to scrape detail {url}: {e}")
            return None
