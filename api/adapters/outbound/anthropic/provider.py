import json
import httpx

from ....domain.models import FeedItem
from ....domain.ports.outbound.services import IAIProvider, ScoreResult, ScrapedItem

SCORE_SYSTEM = """Du bist ein Relevanz-Filter für einen persönlichen News-Aggregator.
Themen: Tech/KI und Sport. Sprachen: Deutsch und Englisch.
Antworte ausschließlich mit einem JSON-Objekt, ohne Markdown-Backticks:
{"score": <0-100>, "reason": "<ein Satz>", "tags": ["<tag>", ...]}"""

SCRAPE_SYSTEM = """Du extrahierst Artikel aus HTML-Seiten.
Antworte ausschließlich mit einem JSON-Array, ohne Markdown-Backticks:
[{"title": "...", "url": "...", "summary": "...", "pub_date": "..."}]
Maximal 10 Artikel. Fehlende Felder als null."""

QUERY_SYSTEM = """Du bist ein präziser News-Analyst. Dir werden aktuelle Schlagzeilen
aus den Bereichen Tech/KI und Sport präsentiert. Antworte direkt und auf den Punkt.
Antworte auf Deutsch, außer der Nutzer fragt explizit auf Englisch."""


class AnthropicProvider(IAIProvider):
    def __init__(self, api_key: str, query_model: str, batch_model: str = "claude-haiku-4-5-20251001"):
        self._api_key = api_key
        self._query_model = query_model
        self._batch_model = batch_model
        self._base_url = "https://api.anthropic.com/v1/messages"

    async def _call(self, model: str, system: str, user: str, max_tokens: int = 512) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self._base_url,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={"model": model, "max_tokens": max_tokens, "system": system,
                      "messages": [{"role": "user", "content": user}]},
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]

    async def score_item(self, title: str, summary: str) -> ScoreResult:
        user = f"Titel: {title}\nZusammenfassung: {summary or '(keine)'}"
        raw = await self._call(self._batch_model, SCORE_SYSTEM, user)
        try:
            data = json.loads(raw)
            return ScoreResult(score=int(data.get("score", 0)), reason=data.get("reason", ""), tags=data.get("tags", []))
        except (json.JSONDecodeError, KeyError, ValueError):
            return ScoreResult(score=0, reason="Parsing-Fehler", tags=[])

    async def scrape_page(self, html: str, source_url: str) -> list[ScrapedItem]:
        raw = await self._call(self._batch_model, SCRAPE_SYSTEM, f"Quell-URL: {source_url}\n\nHTML:\n{html[:8000]}", max_tokens=1024)
        try:
            return [ScrapedItem(title=i.get("title",""), url=i.get("url") or source_url,
                                summary=i.get("summary"), pub_date=i.get("pub_date"))
                    for i in json.loads(raw) if i.get("title")]
        except (json.JSONDecodeError, TypeError):
            return []

    async def query(self, prompt: str, context_items: list[FeedItem]) -> str:
        context = "\n".join(f"- {i.title}: {i.description or ''}" for i in context_items[:30])
        return await self._call(self._query_model, QUERY_SYSTEM,
                                f"Aktuelle Schlagzeilen:\n{context}\n\nFrage: {prompt}", max_tokens=1000)
