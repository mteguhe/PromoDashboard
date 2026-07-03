import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth
from scraper.adapters.base import BaseAdapter

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_SKIP_WORDS = {"hari", "jam", "menit", "bln", "minggu", "detik", "terjemahkan", "disematkan"}

_STEALTH = Stealth()


class SocialAdapter(BaseAdapter):
    def __init__(self, accounts: list[dict]):
        self.accounts = accounts

    def fetch(self) -> list[dict]:
        results = []
        threads_accounts = [a for a in self.accounts if a.get("platform") == "threads"]
        other_accounts = [a for a in self.accounts if a.get("platform") != "threads"]

        if threads_accounts:
            results.extend(self._fetch_all_threads(threads_accounts))

        for account in other_accounts:
            try:
                if account["platform"] == "tiktok":
                    results.extend(self._fetch_tiktok(account))
                else:
                    results.extend(self._fetch_web(account))
            except Exception as e:
                print(f"[SocialAdapter] Skip {account.get('name', '?')}: {e}")

        return results

    def _fetch_all_threads(self, accounts: list[dict]) -> list[dict]:
        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                ctx = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="id-ID",
                    viewport={"width": 1280, "height": 900},
                )
                page = ctx.new_page()
                _STEALTH.apply_stealth_sync(page)

                for account in accounts:
                    try:
                        items = self._fetch_threads_page(page, account)
                        results.extend(items)
                    except Exception as e:
                        print(f"[SocialAdapter] {account.get('name', '?')} error: {e}")

                browser.close()
        except Exception as e:
            print(f"[SocialAdapter] Playwright error: {e}")
        return results

    def _fetch_threads_page(self, page, account: dict) -> list[dict]:
        page.goto(account["url"], wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)

        # Scroll to load more posts
        for _ in range(2):
            page.keyboard.press("End")
            page.wait_for_timeout(2000)

        username = account["url"].rstrip("/").split("@")[-1]

        posts = page.evaluate("""(username) => {
            const containers = document.querySelectorAll('[data-pressable-container]');
            const results = [];
            containers.forEach(el => {
                const text = el.innerText.trim();
                if (text.length < 20) return;
                const link = el.querySelector('a[href*="/post/"]');
                results.push({ text: text.slice(0, 400), href: link ? link.href : '' });
            });
            return results;
        }""", username)

        items = []
        for post in posts:
            if len(post.get("text", "")) < 20:
                continue
            lines = [
                l.strip() for l in post["text"].split("\n")
                if l.strip() and not l.strip().isdigit()
                and l.strip().lower() not in _SKIP_WORDS
                and l.strip() != username
            ]
            # Drop 1-word lines that look like timestamps (e.g. "1hari", "2 hari")
            lines = [l for l in lines if not (len(l) < 10 and any(w in l.lower() for w in _SKIP_WORDS))]
            if not lines:
                continue

            title = lines[0][:255]
            description = "\n".join(lines)[:500]
            href = post.get("href", "")
            source_url = href if href else f"{account['url']}#{abs(hash(title)) % 99999}"

            items.append({
                "title": title,
                "description": description,
                "category": account["category"],
                "brand_name": account.get("name"),
                "promo_code": None,
                "discount_value": None,
                "min_transaction": None,
                "expired_date": None,
                "source_platform": "Threads",
                "source_url": source_url,
            })

        return items

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
