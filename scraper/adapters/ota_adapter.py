import re
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth
from scraper.adapters.base import BaseAdapter

_STEALTH = Stealth()


def _slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower())[:60].strip('-')


class OtaAdapter(BaseAdapter):
    def __init__(self, sources: list):
        self.sources = sources

    def fetch(self) -> list:
        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                ctx = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="id-ID",
                    viewport={"width": 1280, "height": 720},
                )
                page = ctx.new_page()
                _STEALTH.apply_stealth_sync(page)

                for source in self.sources:
                    try:
                        items = self._fetch_source(page, source)
                        results.extend(items)
                    except Exception as e:
                        print(f"[OtaAdapter] {source['name']} error: {e}")

                browser.close()
        except Exception as e:
            print(f"[OtaAdapter] Browser launch failed: {e}")
        return results

    def _fetch_source(self, page, source: dict) -> list:
        try:
            page.goto(source["url"], wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(source.get("wait_ms", 3000))
            page.wait_for_selector(source["selector"], timeout=12000)
        except PlaywrightTimeout:
            print(f"[OtaAdapter] No elements for '{source['name']}' selector '{source['selector']}'")
            return []

        elements = page.query_selector_all(source["selector"])
        base = f"{urlparse(source['url']).scheme}://{urlparse(source['url']).netloc}"
        items = []

        for el in elements[:15]:
            text = el.inner_text().strip()
            if not text or len(text) < 10:
                continue

            lines = [l.strip() for l in text.split('\n') if l.strip()]
            title = lines[0][:255] if lines else text[:80]

            # Prefer the element itself as link (for <a> selectors), else find child link
            href = el.get_attribute("href") or ""
            if not href:
                link_el = el.query_selector("a[href]")
                href = (link_el.get_attribute("href") or "") if link_el else ""

            source_url = urljoin(base, href) if href else f"{source['url']}#{_slug(title)}"

            items.append({
                "title": title,
                "description": text[:500],
                "category": source["category"],
                "brand_name": source.get("platform"),
                "promo_code": None,
                "discount_value": None,
                "min_transaction": None,
                "expired_date": None,
                "source_platform": source.get("platform", "OTA"),
                "source_url": source_url,
            })

        return items
