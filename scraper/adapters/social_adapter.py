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

class SocialAdapter(BaseAdapter):
    def __init__(self, accounts: list[dict]):
        self.accounts = accounts

    def fetch(self) -> list[dict]:
        results = []
        for account in self.accounts:
            try:
                if account["platform"] == "tiktok":
                    results.extend(self._fetch_tiktok(account))
                else:
                    results.extend(self._fetch_web(account))
            except Exception as e:
                print(f"[SocialAdapter] Skip {account.get('name', '?')}: {e}")
        return results

    def _fetch_web(self, account: dict) -> list[dict]:
        resp = requests.get(account["url"], headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[SocialAdapter] {account['name']} → HTTP {resp.status_code}, skipping")
            return []
        soup = BeautifulSoup(resp.content, "html.parser")
        elements = soup.select(account["selector"]) if account.get("selector") else []
        items = []
        for el in elements:
            text = el.get_text(strip=True)[:500]
            if not text:
                continue
            link = el.find("a")
            source_url = link["href"] if link and link.get("href") else account["url"]
            items.append({
                "title": text[:100],
                "description": text,
                "category": account["category"],
                "brand_name": account["name"],
                "promo_code": None,
                "discount_value": None,
                "min_transaction": None,
                "expired_date": None,
                "source_platform": account["platform"],
                "source_url": source_url,
            })
        return items

    def _fetch_tiktok(self, account: dict) -> list[dict]:
        oembed_url = f"https://www.tiktok.com/oembed?url={account['url']}"
        resp = requests.get(oembed_url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        title = data.get("title", "")
        if not title:
            return []
        return [{
            "title": title[:100],
            "description": title,
            "category": account["category"],
            "brand_name": account["name"],
            "promo_code": None,
            "discount_value": None,
            "min_transaction": None,
            "expired_date": None,
            "source_platform": "TikTok",
            "source_url": account["url"],
        }]
