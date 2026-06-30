from scraper.adapters.base import BaseAdapter
from scraper.rss_scraper import fetch_rss_entries, download_page_html, extract_article_text

class RssAdapter(BaseAdapter):
    def __init__(self, sources: list[dict]):
        self.sources = sources

    def fetch(self) -> list[dict]:
        results = []
        for source in self.sources:
            try:
                results.extend(self._fetch_source(source))
            except Exception as e:
                print(f"[RssAdapter] Skip {source.get('name', '?')}: {e}")
        return results

    def _fetch_source(self, source: dict) -> list[dict]:
        entries = fetch_rss_entries(source["url"])
        items = []
        for entry in entries:
            url = entry.get("link", "")
            if not url:
                continue
            title = entry.get("title", "")
            summary = entry.get("description", "")

            html = download_page_html(url)
            article_text = None
            if html:
                article_text = extract_article_text(html, source.get("selector", ""))
            if not article_text:
                article_text = summary

            if not article_text:
                continue

            items.append({
                "title": title[:255],
                "description": article_text[:500],
                "category": source["category"],
                "brand_name": None,
                "promo_code": None,
                "discount_value": None,
                "min_transaction": None,
                "expired_date": None,
                "source_platform": "RSS",
                "source_url": url,
            })
        return items
