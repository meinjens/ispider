import httpx
from ....domain.ports.outbound.services import IFeedFetcher, IAIProvider, ScrapedItem


class WebScraper(IFeedFetcher):
    def __init__(self, ai_provider: IAIProvider):
        self._ai = ai_provider

    async def fetch(self, url: str) -> list[ScrapedItem]:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "iSpider/0.1"})
            resp.raise_for_status()
        return await self._ai.scrape_page(resp.text, url)
