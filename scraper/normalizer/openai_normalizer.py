import json
import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a real estate data extraction agent for the Egyptian market.
Given a raw property listing (which may be mixed English/Arabic), extract the data into a strict JSON format matching our database schema.

Rules:
1. `governorate` MUST be one of: ["cairo", "giza", "alexandria", "qalyubia", "sharqia", "dakahlia", "beheira", "gharbia", "monufia", "kafr_el_sheikh", "damietta", "port_said", "ismailia", "suez", "north_sinai", "south_sinai", "red_sea", "matrouh", "new_valley", "fayoum", "beni_suef", "minya", "assiut", "sohag", "qena", "luxor", "aswan"]
   (e.g., "New Cairo" -> governorate: "cairo", city: "New Cairo". "Sheikh Zayed" -> governorate: "giza", city: "Sheikh Zayed City". "North Coast / Sahel" -> governorate: "matrouh", city: "North Coast". "Hurghada" -> governorate: "red_sea", city: "Hurghada".).
2. `city` is REQUIRED. Always provide a city name string. If unsure, use the most specific location name available (compound name, district, etc).
3. `finishing` MUST be one of: ["core_shell", "semi", "fully", "lux"] or null. If it says "fully finished", use "fully". If "super lux", use "lux".
4. `asking_price` MUST be an integer. Remove commas/currencies. If it says "1.5 million", use 1500000.
5. `area_sqm` MUST be a number.
6. If `bedrooms` or `bathrooms` are missing, infer from text if possible, else 0.
7. `property_type` is REQUIRED. Extract the property type (e.g., "Apartment", "Chalet", "Villa", "Townhouse", "Penthouse", "Twin House", "Duplex"). If missing, infer it from the title or description.
8. Return ONLY valid JSON, nothing else. No markdown formatting.
"""

class OpenAINormalizer:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.is_mock = not self.api_key or self.api_key.endswith('xyz123')
        if self.is_mock:
            logger.warning("OPENAI_API_KEY is missing or dummy. Using MOCK normalizer for testing.")
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def normalize(self, raw_listing: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_mock:
            # Return dummy normalized data for end-to-end testing without GPT
            title = raw_listing.get("title")
            if not title:
                title = "Mock Scraped Property"
                
            normalized = {
                "type": "scraped",
                "title": title[:200],
                "description": raw_listing.get("description") or "Mock Description",
                "governorate": "cairo",
                "city": "New Cairo",
                "property_type": raw_listing.get("property_type") or "Apartment",
                "area_sqm": raw_listing.get("area_sqm") or 100,
                "bedrooms": raw_listing.get("bedrooms") or 2,
                "bathrooms": raw_listing.get("bathrooms") or 1,
                "asking_price": raw_listing.get("raw_price") or 1000000,
                "currency": "EGP",
                "negotiable": True
            }
        else:
            prompt = f"Raw Listing Data:\n{json.dumps(raw_listing, ensure_ascii=False, indent=2)}\n\nExtract into JSON."
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={ "type": "json_object" }
                )
                content = response.choices[0].message.content
                normalized = json.loads(content)
            except Exception as e:
                logger.error(f"OpenAI Normalization failed: {e}")
                raise

        # Add back source fields that GPT doesn't need to touch
        normalized['source_site'] = raw_listing.get('source_site')
        normalized['source_url'] = raw_listing.get('source_url')
        normalized['source_seller_name'] = raw_listing.get('source_seller_name')
        normalized['source_seller_phone'] = raw_listing.get('source_seller_phone')
        
        # Fallback if OpenAI missed the title
        if not normalized.get('title'):
            normalized['title'] = raw_listing.get('title') or "Scraped Property"
            
        # Fallback if OpenAI missed property_type
        if not normalized.get('property_type'):
            normalized['property_type'] = raw_listing.get('property_type') or "Unknown"
        
        # Fallback if OpenAI missed the city — extract from raw_address
        if not normalized.get('city'):
            raw_addr = raw_listing.get('raw_address', '')
            if raw_addr:
                # Use the first part of the address as city
                parts = [p.strip() for p in raw_addr.split(',')]
                normalized['city'] = parts[-1] if parts else "Unknown"
            else:
                normalized['city'] = "Unknown"
        
        # Fallback if OpenAI missed governorate
        if not normalized.get('governorate'):
            normalized['governorate'] = "cairo"
            
        return normalized
