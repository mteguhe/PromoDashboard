from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from scraper.adapters.base import BaseAdapter

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

class PortalAdapter(BaseAdapter):
    def __init__(self, sources: list[dict]):
        self.sources = sources

    def fetch(self) -> list[dict]:
        results = []
        for source in self.sources:
            try:
                results.extend(self._fetch_source(source))
            except Exception as e:
                print(f"[PortalAdapter] Skip {source.get('name', '?')}: {e}")
        return results

    def _fetch_source(self, source: dict) -> list[dict]:
        resp = requests.get(source["url"], headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[PortalAdapter] {source['name']} → HTTP {resp.status_code}, skipping")
            return []
        soup = BeautifulSoup(resp.content, "html.parser")
        elements = soup.select(source["selector"])
        if not elements:
            print(f"[PortalAdapter] No elements for '{source['name']}' selector '{source['selector']}'")
            return []

        base = urlparse(source["url"])
        items = []
        for el in elements:
            title = el.get_text(strip=True)[:255]
            if not title:
                continue
            link = el.find("a")
            href = link["href"] if link and link.get("href") else source["url"]
            if href.startswith("/"):
                href = f"{base.scheme}://{base.netloc}{href}"
            items.append({
                "title": title,
                "description": title,
                "category": source["category"],
                "brand_name": source.get("name"),
                "promo_code": None,
                "discount_value": None,
                "min_transaction": None,
                "expired_date": None,
                "source_platform": source["name"],
                "source_url": href,
            })
        return items
