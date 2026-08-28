# Dawwar AI Property Scraper

This is a standalone Python microservice that crawls external real estate websites (PropertyFinder, Dubizzle), normalizes their messy data using OpenAI (GPT-4o-mini), downloads images, and automatically publishes the listings to the main Dawwar Django API.

## 🏗️ Architecture

The pipeline consists of the following components:

1. **Scrapers (`scrapers/`)**: 
   - **`PropertyFinderScraper`**: Very fast! It extracts structured `JSON-LD` schemas directly from the HTML source without needing a browser. It also simulates API calls to grab the seller's phone number.
   - **`DubizzleScraper`**: Uses `Playwright` (headless browser) to render JavaScript and automatically click "Show Phone Number" buttons.
2. **Normalizer (`normalizer/`)**: Passes the raw, unstructured Egyptian real estate data to OpenAI. It normalizes locations (e.g. converting "Sheikh Zayed" into Governorate: "Giza") and returns a clean, strict JSON that matches Dawwar's API requirements.
3. **Downloader (`downloader/`)**: Downloads image URLs locally to temporary storage.
4. **Publisher (`publisher/`)**: Acts as an authenticated Dawwar HTTP client. It posts the JSON data to `/api/listings/scrape-import/`, retrieves the new listing ID, and then posts the local images to `/api/listings/{id}/upload-media/`.
5. **Storage (`storage/seen_urls.db`)**: A lightweight SQLite database that tracks every URL the scraper has ever processed to ensure it never scrapes or publishes duplicates.
6. **Scheduler (`scheduler.py`)**: Uses `APScheduler` to run the scrapers periodically (e.g., every 6 hours) completely hands-free.

---

## ⚙️ Setup Instructions

This microservice requires Python 3.12+ and runs completely independently from Django.

### 1. Create a Virtual Environment
```bash
cd e:\projects\homi\scraper
python -m venv venv
.\venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill it out:

```env
# Point to your local or production Dawwar Django backend
DAWWAR_API_URL=http://localhost:8000/api

# The JWT token generated for the AI Bot user. 
# Run `python manage.py create_ai_user` in the backend to get this!
DAWWAR_BOT_TOKEN=eyJhbGciOiJIUzI1NiIsIn...

# Your actual ChatGPT / OpenAI Key
OPENAI_API_KEY=sk-proj-YOUR-REAL-KEY
```

> **Note**: If you leave `OPENAI_API_KEY` empty or use a dummy key, the scraper will automatically fallback to a **Mock Normalizer**. This is useful for testing the pipeline without spending OpenAI credits.

---

## 🚀 How to Run

### Option 1: Manual Test Run (Recommended for testing)
To run a quick test that processes 1 page of results (approx. 25 listings) and stops:
```bash
.\venv\Scripts\activate
python main.py
```
This is the best way to debug and verify that listings are appearing in your Django database.

### Option 2: Run the Background Scheduler
To run the scraper continuously as a background worker:
```bash
.\venv\Scripts\activate
python scheduler.py
```
This will boot up `APScheduler` and run the scraper pipeline automatically based on the intervals defined in `scheduler.py` (default: every 6 hours).

---

## 🧹 Database Reset

If you want to force the scraper to re-process listings it has already seen (for example, if you deleted them from the Django DB and want them back), just delete the SQLite deduplication file:

```bash
rm storage\seen_urls.db
```
The scraper will recreate it on the next run.
