# filepath: scraper/scrape_single.py
import sys
import os
import json
import requests
from bs4 import BeautifulSoup
from scraper.db_manager import DatabaseManager
from scraper.ai_parser import parse_with_gemini
from scraper.parser import parse_promo_text
from scraper.rss_scraper import _get_headers

def scrape_single_url_with_text(url, text, title=None, db_path="promo.db"):
    try:
        # Determine Category
        lowered = text.lower()
        if any(w in lowered for w in ["flight", "penerbangan", "tiket pesawat", "maskapai", "jakarta", "shanghai", "guangzhou", "pp", "china"]):
            category = "flight"
        elif any(w in lowered for w in ["nonton", "cinema", "bioskop", "xxi", "cgv", "dufan"]):
            category = "entertainment"
        elif any(w in lowered for w in ["baju", "sepatu", "fashion", "uniqlo", "h&m"]):
            category = "fashion"
        elif any(w in lowered for w in ["pameran", "event", "expo", "festival"]):
            category = "event"
        else:
            category = "food"
            
        # Parse promo details (AI -> Regex)
        parsed = None
        if os.environ.get("GEMINI_API_KEY"):
            parsed = parse_with_gemini(text, category=category)
            
        if not parsed:
            parsed = parse_promo_text(text, category=category)
            
        # Add metadata
        platform = "Social Media"
        if "threads.net" in url or "threads.com" in url:
            platform = "Threads"
        elif "instagram.com" in url:
            platform = "Instagram"
        elif "twitter.com" in url or "x.com" in url:
            platform = "Twitter"
            
        parsed.update({
            "title": title.strip() if title else (parsed.get("title") or text.split("\n")[0][:100]),
            "description": text.strip(),
            "source_platform": platform,
            "source_url": url
        })
        
        # Save to DB
        parsed["category"] = category
        if not parsed.get("brand_name") and parsed.get("airline"):
            parsed["brand_name"] = parsed["airline"]
        with DatabaseManager(db_path) as db_mgr:
            db_mgr.insert_promo(parsed)
                
        return {"success": True, "data": parsed}
    except Exception as e:
        return {"success": False, "error": str(e)}

def scrape_single_url(url, db_path="promo.db"):
    try:
        # 1. Fetch URL HTML
        response = requests.get(url, headers=_get_headers(), timeout=15)
        if response.status_code != 200:
            return {"success": False, "error": f"Failed to fetch URL. Status code: {response.status_code}"}
            
        # 2. Extract og:description and og:title
        soup = BeautifulSoup(response.content, "html.parser")
        
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        og_title = soup.find("meta", attrs={"property": "og:title"})
        
        text = og_desc["content"] if og_desc else None
        if not text:
            desc_meta = soup.find("meta", attrs={"name": "description"})
            text = desc_meta["content"] if desc_meta else None
            
        title = og_title["content"] if og_title else None
        if not title:
            title = soup.title.string if soup.title else "Promo dari Sosial Media"
            
        if not text:
            # Fallback to general text extraction
            from scraper.rss_scraper import extract_article_text
            text = extract_article_text(response.text, "")
            
        if not text:
            return {"success": False, "error": "Could not extract text from the URL."}
            
        return scrape_single_url_with_text(url, text, title, db_path)
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No URL provided."}))
        sys.exit(1)
        
    url = sys.argv[1]
    
    # Check if text is provided via stdin
    text_input = None
    if not sys.stdin.isatty():
        text_input = sys.stdin.read().strip()
        
    if text_input:
        # Use provided text directly
        result = scrape_single_url_with_text(url, text_input)
    else:
        # Scrape from URL
        result = scrape_single_url(url)
        
    print(json.dumps(result))
