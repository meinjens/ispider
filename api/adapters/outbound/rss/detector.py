import httpx
from api.domain.models import SourceType


RSS_CONTENT_TYPES = {
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
}


async def detect_source_type(url: str) -> SourceType:
    """
    Prüft eine URL und gibt SourceType.RSS oder SourceType.WEB zurück.
    Strategie:
      1. Content-Type Header → RSS wenn bekannter Feed-Typ
      2. HTML <link rel="alternate"> → RSS-Link extrahieren
      3. Sonst → WEB
    """
    async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": "iSpider/0.1"})
            resp.raise_for_status()
        except httpx.HTTPError:
            return SourceType.WEB

    content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type in RSS_CONTENT_TYPES:
        return SourceType.RSS

    # Einfacher HTML-Check auf alternate-Link
    if "text/html" in content_type:
        text = resp.text[:4096]
        if 'type="application/rss+xml"' in text or 'type="application/atom+xml"' in text:
            return SourceType.RSS

    return SourceType.WEB
