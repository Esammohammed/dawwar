import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DAWWAR_API_URL = os.getenv("DAWWAR_API_URL", "http://localhost:8000/api")
DAWWAR_BOT_TOKEN = os.getenv("DAWWAR_BOT_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SCRAPE_PAGES_LIMIT = int(os.getenv("SCRAPE_PAGES_LIMIT", 500))
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "storage" / "seen_urls.db"))
MEDIA_DIR = os.getenv("MEDIA_DIR", str(BASE_DIR / "media"))

os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
