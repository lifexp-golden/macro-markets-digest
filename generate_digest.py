import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
import feedparser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_ticker_quote(symbol):
    """Fetches fast market data using public quote endpoints with fallback headers."""
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        df = t.history(period="2d")
        if not df.empty:
            curr = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) > 1 else curr
            pct = ((curr - prev) / prev) * 100 if prev else 0.0
            return f"{curr:,.2f}", f"{'+' if pct >= 0 else ''}{pct:.2f}%"
    except Exception:
        pass
    return "—", "0.00%"

def fetch_vitals():
    symbols = {
        "nifty": "^NSEI",
        "sensex": "^BSESN",
        "usd_inr": "INR=X",
        "sp500": "^GSPC",
        "us10y": "^TNX",
        "brent": "BZ=F"
    }
    vitals = {}
    for key, sym in symbols.items():
        val, delta = fetch_ticker_quote(sym)
        vitals[key] = {"value": val, "delta": delta}
    return vitals

def fetch_feed(url, max_items=3):
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read()
        feed = feedparser.parse(content)
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "No details available.")).strip()
            if "<" in summary:
                import re
                summary = re.sub(r'<[^>]+>', '', summary)
            items.append({
                "title": title,
                "summary": (summary[:180] + "...") if len(summary) > 180 else summary,
                "link": entry.get("link", "#"),
                "source": feed.feed.get("title", "Wire")
            })
    except Exception:
        pass
    return items

def main():
    vitals = fetch_vitals()
    
    # Cloud-friendly financial wire RSS URLs
    india_news = fetch_feed("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", 3)
    us_news = fetch_feed("https://finance.yahoo.com/news/rssindex", 3)
    global_news = fetch_feed("https://www.cnbc.com/id/100003114/device/rss/rss.html", 3)

    digest_payload = {
        "date": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S IST"),
        "vitals": vitals,
        "india": india_news if india_news else [{"title": "Indian Markets Opening Session", "summary": "Markets tracking global cues and earnings prints.", "link": "#", "source": "ET Markets"}],
        "us": us_news if us_news else [{"title": "Wall Street Opening Wire", "summary": "Treasury yields and index futures monitor macro policy.", "link": "#", "source": "Yahoo Finance"}],
        "global": global_news if global_news else [{"title": "Global Central Bank Watch", "summary": "Monitoring rate trajectories and commodity trade balances.", "link": "#", "source": "CNBC"}]
    }

    with open("today.json", "w", encoding="utf-8") as f:
        json.dump(digest_payload, f, indent=2, ensure_ascii=False)
        
    return digest_payload

if __name__ == "__main__":
    main()
