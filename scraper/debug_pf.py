"""Debug script to analyze the PropertyFinder search results page structure."""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        await page.goto("https://www.propertyfinder.eg/en/buy/properties-for-sale.html?page=1", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        # 1. Check if bot-blocked
        title_text = soup.title.string if soup.title and soup.title.string else "NO TITLE"
        print(f"\n=== PAGE TITLE: {title_text} ===\n")
        
        if "human" in title_text.lower():
            print("BOT BLOCKED! Page shows captcha.")
            await browser.close()
            return
        
        # 2. Look for JSON-LD on search results page
        scripts = soup.find_all("script", type="application/ld+json")
        print(f"Found {len(scripts)} JSON-LD scripts")
        for i, s in enumerate(scripts):
            text = s.string if s.string else "EMPTY"
            print(f"--- Script {i} (first 300 chars) ---")
            print(text[:300])
            print()
        
        # 3. Look for listing cards
        cards = soup.select('a[href*="/plp/"]')
        print(f"\nFound {len(cards)} listing links")
        
        # 4. Look for data in Next.js __NEXT_DATA__
        next_data = soup.find("script", id="__NEXT_DATA__")
        if next_data:
            print("\n=== __NEXT_DATA__ found! ===")
            try:
                data = json.loads(next_data.string)
                # Try to find listings in the page props
                props = data.get("props", {}).get("pageProps", {})
                print(f"pageProps keys: {list(props.keys())[:10]}")
                # Look for search results
                for key in props:
                    val = props[key]
                    if isinstance(val, dict) and "hits" in val:
                        hits = val["hits"]
                        print(f"\nFound 'hits' under '{key}': {len(hits)} items")
                        if hits:
                            print(f"First hit keys: {list(hits[0].keys())}")
                            print(f"First hit (500 chars): {json.dumps(hits[0], ensure_ascii=False)[:500]}")
                    elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        print(f"\nFound list under '{key}': {len(val)} items, first keys: {list(val[0].keys())[:10]}")
            except Exception as e:
                print(f"Error parsing __NEXT_DATA__: {e}")
        else:
            print("\nNo __NEXT_DATA__ script found")
        
        # 5. Look for images on the page
        all_imgs = soup.find_all("img")
        cdn_imgs = [img for img in all_imgs if img.get("src", "").startswith("http")]
        print(f"\nTotal <img> tags: {len(all_imgs)}, with http src: {len(cdn_imgs)}")
        for img in cdn_imgs[:5]:
            print(f"  src: {img.get('src', '')[:120]}")
        
        # Save full HTML for inspection
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("\nFull HTML saved to debug_page.html")
        
        await browser.close()

asyncio.run(main())
