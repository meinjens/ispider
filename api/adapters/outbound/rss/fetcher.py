import re
import httpx
import feedparser
from ....domain.ports.outbound.services import IFeedFetcher, ScrapedItem


class RssFetcher(IFeedFetcher):
    async def fetch(self, url: str) -> list[ScrapedItem]:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "iSpider/0.1"})
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        items = []
        for entry in feed.entries[:20]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            summary = re.sub(r"<[^>]+>", " ", entry.get("summary") or entry.get("description") or "").strip()[:500]
            if title and link:
                items.append(ScrapedItem(title=title, url=link, summary=summary or None,
                                         pub_date=entry.get("published") or entry.get("updated")))
        return items
