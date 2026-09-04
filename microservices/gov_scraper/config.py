import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DAWWAR_API_URL = os.getenv("DAWWAR_API_URL", "http://localhost:8000/api")
DAWWAR_BOT_TOKEN = os.getenv("DAWWAR_BOT_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# How many candidate article links per source to fetch per run — this
# controls scraping depth, not AI spend: the is_housing_related() gate
# (matcher.py) filters out irrelevant articles before any GPT/embedding
# call, so raising this only costs more (cheap) HTTP fetches to the source,
# not more AI cost. Found in real use that 15 was too shallow on busy
# general-news sources (Dostor, aqaar24) — most of a run's budget was
# getting used up on sports/celebrity news before ever reaching housing
# content further down the page. 40 gives real headroom on those sources
# without meaningfully slowing a run (each fetch is a plain HTTP GET).
MAX_ARTICLES_PER_SOURCE = int(os.getenv("MAX_ARTICLES_PER_SOURCE", 40))

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "storage" / "seen_urls.db"))

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
