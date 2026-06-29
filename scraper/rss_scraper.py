import requests
import feedparser
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_rss_entries(feed_url):
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(feed_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        
        feed = feedparser.parse(response.content)
        entries = []
        for entry in feed.entries:
            entries.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "description": entry.get("summary", entry.get("description", ""))
            })
        return entries
    except Exception as e:
        print(f"Error fetching RSS {feed_url}: {e}")
        return []

def extract_article_text(html_content, css_selector):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Hapus elemen skrip, gaya, iframe, dan iklan
        for element in soup(["script", "style", "iframe", "noscript"]):
            element.decompose()
            
        # Cari area teks artikel utama
        target_area = None
        if css_selector and css_selector.strip():
            selectors = [s.strip() for s in css_selector.split(",") if s.strip()]
            for selector in selectors:
                target_area = soup.select_one(selector)
                if target_area:
                    break
            if not target_area:
                return ""
        else:
            target_area = soup.body if soup.body else soup
            
        text = target_area.get_text(separator=" ")
        # Bersihkan whitespace berlebih
        cleaned_text = " ".join(text.split())
        return cleaned_text
    except Exception as e:
        print(f"Error extracting article text: {e}")
        return ""

def download_page_html(url):
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
        return ""
    except Exception as e:
        print(f"Error downloading page {url}: {e}")
        return ""
