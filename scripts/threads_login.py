"""
Interactive Threads login helper.

Usage:
    python scripts/threads_login.py

Sets up threads_session.json so the main scraper can run without
re-logging in each time.  Run this once after setting THREADS_USERNAME
and THREADS_PASSWORD in your .env file.
"""

import os
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from scraper.threads_session import ensure_logged_in, has_credentials, SESSION_FILE

_STEALTH = Stealth()


def main():
    if not has_credentials():
        print("ERROR: THREADS_USERNAME and THREADS_PASSWORD must be set in .env")
        print("  cp .env.example .env  then fill in the values")
        sys.exit(1)

    print("Starting Playwright browser to log into Threads...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # visible so you can solve CAPTCHA if needed
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

        success = ensure_logged_in(page, ctx)
        if success:
            print(f"\n✅ Login successful! Session saved to {SESSION_FILE}")
            print("   You can now run: python -m scraper.engine")
        else:
            print("\n❌ Login failed. Check your credentials in .env")

        input("\nPress Enter to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()
