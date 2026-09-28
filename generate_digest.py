import json
import re
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
import feedparser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_google_finance_quote(ticker_path):
    """
    Fetches real-time price & daily change directly from Google Finance pages.
    ticker_path format: 'INDEXBOM:SENSEX', 'NIFTY_50:INDEXNSE', 'USD-INR', etc.
    """
    url = f"https://www.google.com/finance/quote/{ticker_path}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=7) as response:
            html = response.read().decode("utf-8", errors="ignore")
        
        # Extract live price
        price_match = re.search(r'data-last-price="([^"]+)"', html)
        if not price_match:
            price_match = re.search(r'class="YMlKec fxKbKc">([^<]+)<', html)
        price = price_match.group(1).replace(",", "") if price_match else None
        
        # Extract percentage change
        pct_match = re.search(r'aria-label="[a-zA-Z\s]+by\s+([0-9\.]+%|\-[0-9\.]+\%)"', html)
        if not pct_match:
            pct_match = re.search(r'class="JwB6be[^"]*">([^<]*%?)<', html)
        pct = pct_match.group(1) if pct_match else "0.00%"

        if price:
            val_num = float(re.sub(r'[^\d.]', '', price))
            sign = "+" if not pct.startswith("-") and not pct.startswith("+") else ""
            return f"{val_num:,.2f}", f"{sign}{pct}"
    except Exception:
        pass
    return "—", "0.00%"

def fetch_vitals():
    mappings = {
        "nifty": "NIFTY_50:INDEXNSE",
        "sensex": "INDEXBOM:SENSEX",
        "usd_inr": "USD-INR",
        "sp500": ".INX:INDEXSP",
        "us10y": "TNX:INDEXCBOE",
        "brent": "BZ00:NYMEX"
    }
    vitals = {}
    for key, path in mappings.items():
        val, delta = fetch_google_finance_quote(path)
        vitals[key] = {"value": val, "delta": delta}
    return vitals

def fetch_feed(url, fallback_source, max_items=3):
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=7) as response:
            feed = feedparser.parse(response.read())
            
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "Click to read full market coverage.")).strip()
            # Strip HTML tags
            summary = re.sub(r'<[^>]+>', '', summary).replace("&nbsp;", " ")
            if len(summary) > 160:
                summary = summary[:160] + "..."
                
            items.append({
                "title": title if title else "Market Update",
                "summary": summary if summary else "Live coverage of market movements and economic trends.",
                "link": entry.get("link", "#"),
                "source": feed.feed.get("title", fallback_source)
            })
    except Exception:
        pass
    
    # If feed fails, provide clean default cards
    if not items:
        items = [{
            "title": f"{fallback_source} Wire",
            "summary": "Tracking live session moves, earnings, and central bank developments.",
            "link": "#",
            "source": fallback_source
        }]
    return items

def main():
    vitals = fetch_vitals()
    
    # Direct, reliable financial news feeds
    india_news = fetch_feed("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "ET Markets")
    us_news = fetch_feed("https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=markets&sort=date", "CNBC")
    global_news = fetch_feed("https://feeds.content.dowjones.io/public/rss/mw_topstories", "MarketWatch")

    digest_payload = {
        "date": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S IST"),
        "vitals": vitals,
        "india": india_news,
        "us": us_news,
        "global": global_news
    }

    with open("today.json", "w", encoding="utf-8") as f:
        json.dump(digest_payload, f, indent=2, ensure_ascii=False)

    return digest_payload

if __name__ == "__main__":
    main()
