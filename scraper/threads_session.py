"""
Threads login + session persistence.

On first run (or when session expires), logs in with THREADS_USERNAME /
THREADS_PASSWORD from environment and saves the browser storage state to
threads_session.json.  Subsequent runs reuse the saved cookies so the
scraper never logs in more than necessary.
"""

import json
import os
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth

SESSION_FILE = Path("threads_session.json")
_STEALTH = Stealth()

_LOGIN_URL = "https://www.threads.com/login"
_HOME_URL = "https://www.threads.com/"


def _credentials() -> tuple[str, str]:
    username = os.environ.get("THREADS_USERNAME", "")
    password = os.environ.get("THREADS_PASSWORD", "")
    return username, password


def has_credentials() -> bool:
    u, p = _credentials()
    return bool(u and p)


def _is_logged_in(page: Page) -> bool:
    """True when the current page is not the login/signup screen."""
    if "login" in page.url or "accounts" in page.url:
        return False
    # A logged-in Threads page always has the sidebar nav
    return page.query_selector('[aria-label="Home"], [href="/"]') is not None


def _do_login(page: Page) -> bool:
    """Fill and submit the login form. Returns True on success."""
    username, password = _credentials()
    if not username or not password:
        print("[ThreadsSession] No credentials set — set THREADS_USERNAME / THREADS_PASSWORD in .env")
        return False

    try:
        page.goto(_LOGIN_URL, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)

        # Threads login form selectors (Meta sometimes changes these)
        user_sel = 'input[autocomplete="username"], input[name="username"], input[type="text"]'
        pass_sel = 'input[autocomplete="current-password"], input[type="password"]'
        submit_sel = 'button[type="submit"]'

        page.wait_for_selector(user_sel, timeout=10000)
        page.fill(user_sel, username)
        page.wait_for_timeout(800)
        page.fill(pass_sel, password)
        page.wait_for_timeout(800)
        page.click(submit_sel)

        # Wait for redirect away from login page
        page.wait_for_function(
            "() => !window.location.href.includes('/login')",
            timeout=20000,
        )
        page.wait_for_timeout(4000)

        if _is_logged_in(page):
            print("[ThreadsSession] Login successful")
            return True
        else:
            print(f"[ThreadsSession] Login may have failed — current URL: {page.url}")
            return False

    except PlaywrightTimeout as e:
        print(f"[ThreadsSession] Login timed out: {e}")
        return False
    except Exception as e:
        print(f"[ThreadsSession] Login error: {e}")
        return False


def load_session(ctx: BrowserContext) -> bool:
    """
    Load saved session cookies into context.
    Returns True if a session file was found (validity not guaranteed until
    a page is loaded and _is_logged_in() is checked).
    """
    if not SESSION_FILE.exists():
        return False
    try:
        state = json.loads(SESSION_FILE.read_text())
        ctx.add_cookies(state.get("cookies", []))
        print("[ThreadsSession] Loaded saved session from file")
        return True
    except Exception as e:
        print(f"[ThreadsSession] Could not load session: {e}")
        return False


def save_session(ctx: BrowserContext) -> None:
    """Persist current browser context (cookies + localStorage) to file."""
    try:
        ctx.storage_state(path=str(SESSION_FILE))
        print("[ThreadsSession] Session saved")
    except Exception as e:
        print(f"[ThreadsSession] Could not save session: {e}")


def ensure_logged_in(page: Page, ctx: BrowserContext) -> bool:
    """
    Make sure the browser is logged into Threads.

    Flow:
    1. If session file exists, load it and verify with a quick GET to /
    2. If not logged in (expired / no file), do a fresh login and save session
    3. If no credentials available, skip login (anonymous scraping only)

    Returns True if logged in, False if anonymous.
    """
    if not has_credentials():
        print("[ThreadsSession] No credentials — running in anonymous mode")
        return False

    # Try loading saved session first
    had_session = load_session(ctx)

    if had_session:
        # Verify it's still valid
        try:
            page.goto(_HOME_URL, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)
            if _is_logged_in(page):
                print("[ThreadsSession] Existing session is valid")
                return True
            else:
                print("[ThreadsSession] Saved session has expired — re-logging in")
        except Exception:
            print("[ThreadsSession] Session check failed — re-logging in")

    # Perform fresh login
    success = _do_login(page)
    if success:
        save_session(ctx)
    return success
