import json
import logging
from typing import Dict, Any

from openai import AsyncOpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Deliberately narrow scope — see dawwar-govfeed-scraper-plan.md §3: this
# model is only ever an EXTRACTOR of what the article text already says,
# never a source of independent facts about a government program. Getting
# "required documents" wrong is a real citizen-facing harm (someone shows up
# to apply with missing paperwork based on our bad guess), so `requirements`
# must come back null whenever the article doesn't explicitly state
# conditions — that's the correct answer far more often than not, and the
# prompt says so directly rather than nudging the model to always fill it in.
SYSTEM_PROMPT = """
You are a summarization and extraction assistant for Egyptian government
housing news, writing in Arabic. Given a raw scraped news article (title +
body/excerpt), return STRICT JSON with exactly these keys:

{
  "title": "<cleaned, publication-ready Arabic title, max ~150 chars>",
  "ai_summary": "<2-3 sentence Arabic summary of what the article says>",
  "requirements": ["<verbatim condition or required document>", ...] or null,
  "mentioned_program_name": "<exact name of a specific named government housing initiative/program, as stated in the text, or null>"
}

Rules:
1. `ai_summary` must only restate facts present in the source text — do not
   add context, dates, prices, or unit counts the article didn't state.
2. `requirements` — extract ONLY if the article text explicitly names
   required papers/documents or eligibility conditions (e.g. "يشترط تقديم
   بطاقة الرقم القومي", "يجب ألا يكون قد حصل على وحدة مدعومة من قبل"). If the
   article does not mention any such thing, `requirements` MUST be null —
   never infer, guess, or fill in what a program "probably" requires from
   general knowledge. This is the single most important rule: when in
   doubt, return null.
3. `mentioned_program_name` — this is a SUGGESTION for a human to review,
   never used to auto-create anything, so err toward including it: if the
   article names a specific housing initiative/program (not just "وزارة
   الإسكان" doing something general), quote its name as written. If no
   specific program is named, this MUST be null.
4. Return ONLY valid JSON, no markdown formatting, no commentary.
"""


class OpenAINormalizer:
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.is_mock = not self.api_key or self.api_key.endswith('xyz123')
        if self.is_mock:
            logger.warning("OPENAI_API_KEY is missing or dummy. Using MOCK normalizer for testing.")
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    async def normalize(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
        title = raw_article.get("title") or "Untitled"
        body = raw_article.get("body") or ""

        if self.is_mock:
            # No LLM call — deterministic passthrough for end-to-end testing
            # without spending tokens. Never fabricates requirements.
            normalized = {
                "title": title[:150],
                "ai_summary": body[:280] if body else None,
                "requirements": None,
                "mentioned_program_name": None,
            }
        else:
            prompt = f"Title: {title}\n\nBody:\n{body}\n\nExtract into the required JSON."
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                normalized = json.loads(content)
            except Exception as exc:
                logger.error("OpenAI normalization failed: %s", exc)
                raise

        if not normalized.get("title"):
            normalized["title"] = title[:150]

        # `body` is the raw scraped excerpt (Announcement.body — the actual
        # article text/excerpt), distinct from `ai_summary` (the model's
        # 2-3 sentence summary of it) — the normalizer only ever produces
        # the summary and requirements; the raw body passes through as-is.
        normalized["body"] = body

        return normalized
