"""
Layer 2 of the program matcher: semantic similarity, for programs whose name
doesn't fit Layer 1's regex/literal patterns (matcher.py) — e.g. a genuinely
new initiative, or a familiar one phrased differently than expected.

Deliberately built on a fixed numeric comparison (cosine similarity against
pre-computed embeddings), not a generative LLM judgment — that keeps this
layer from reintroducing the classification-drift risk the deterministic
Layer 1 was built to avoid (see matcher.py's docstring): the same input
always scores the same way, it doesn't vary run to run.

Compares against whatever government Project rows *currently exist* in
Dawwar (fetched live from the API each pipeline run, not hardcoded) — so
when staff confirm a Layer 3 AI suggestion by creating a new Project via
admin, this layer starts catching future articles about it automatically,
with zero code changes here.
"""
from __future__ import annotations

import logging
import math
from typing import Optional

import httpx
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, DAWWAR_API_URL

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"

# Calibrated against real output from this pipeline (3 probes x 5 seeded
# programs, text-embedding-3-small): genuinely related Arabic news text
# scored 0.50-0.63 against the right program's name+description, unrelated
# content scored 0.11-0.22 — a wide, clean gap, just centered much lower
# than a naive guess would suggest. 0.45 sits in that gap with margin on
# both sides. Still only a handful of real examples, not a rigorous
# calibration — revisit once more real runs accumulate, especially if a
# genuinely unrelated article starts scoring above this.
SIMILARITY_THRESHOLD = 0.45


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticProgramMatcher:
    """An enhancement layer, not a required one — disabled (matches nothing,
    never raises) whenever OPENAI_API_KEY isn't set, same mock-mode
    philosophy as normalizer/openai_normalizer.py."""

    def __init__(self):
        self.enabled = bool(OPENAI_API_KEY) and not OPENAI_API_KEY.endswith('xyz123')
        self._client = AsyncOpenAI(api_key=OPENAI_API_KEY) if self.enabled else None
        self._projects: list[dict] = []  # [{slug, name, embedding}, ...]

    async def load_projects(self) -> None:
        """Fetch current government Project rows and embed their names once
        per pipeline run. Call before the first match() call."""
        if not self.enabled:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{DAWWAR_API_URL}/projects/", params={"type": "government"}, timeout=20.0
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.warning("Semantic matcher: failed to load Projects, disabling for this run: %s", exc)
            self._projects = []
            return

        projects = data.get("results", data)
        if not projects:
            self._projects = []
            return

        # Name + description gives the embedding more to work with than the
        # bare name alone.
        reference_texts = [
            f"{p['name']}. {p.get('description') or ''}".strip() for p in projects
        ]
        try:
            embeddings = await self._embed_batch(reference_texts)
        except Exception as exc:
            logger.warning("Semantic matcher: failed to embed reference projects, disabling for this run: %s", exc)
            self._projects = []
            return

        self._projects = [
            {"slug": p["slug"], "name": p["name"], "embedding": emb}
            for p, emb in zip(projects, embeddings)
        ]
        logger.info("Semantic matcher: loaded %d reference programs.", len(self._projects))

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [d.embedding for d in resp.data]

    async def match(self, title: str, body: str) -> Optional[tuple[str, str]]:
        """Best-matching (slug, name) if similarity clears the threshold,
        else None. Never raises — a failure here just means "no semantic
        match this time," not a pipeline crash.

        Returns the matched Project's `name` alongside its slug specifically
        so the caller can cross-check it against the normalizer's
        mentioned_program_name (see main.py) — real testing found this
        layer alone isn't precise enough to auto-link on its own: a
        completely fictional program ("مبادرة سكني الجديد") scored 0.534
        against بيتك في مصر, squarely inside the same range as genuine
        paraphrase matches (0.50-0.63) — the two are structurally
        inseparable by similarity score alone, since both are just
        "government housing initiative"-shaped text. Confirming against
        what the article literally names catches this false-positive class
        that no threshold on this signal alone can.
        """
        if not self.enabled or not self._projects:
            return None
        try:
            [article_embedding] = await self._embed_batch([f"{title}. {body}".strip()])
        except Exception as exc:
            logger.warning("Semantic matcher: failed to embed article, skipping: %s", exc)
            return None

        best_slug, best_name, best_score = None, None, 0.0
        for p in self._projects:
            score = _cosine_similarity(article_embedding, p["embedding"])
            if score > best_score:
                best_slug, best_name, best_score = p["slug"], p["name"], score

        if best_slug and best_score >= SIMILARITY_THRESHOLD:
            logger.info("Semantic candidate: %.2f similarity -> %s", best_score, best_slug)
            return (best_slug, best_name)
        return None
