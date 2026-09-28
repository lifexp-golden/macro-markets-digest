import json
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf
import feedparser

def fetch_vitals():
    tickers = {
        "nifty": "^NSEI",
        "sensex": "^BSESN",
        "usd_inr": "INR=X",
        "sp500": "^GSPC",
        "us10y": "^TNX",
        "brent": "BZ=F"
    }
    vitals = {}
    for key, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                pct = ((current - prev) / prev) * 100
            elif len(hist) == 1:
                current = float(hist["Close"].iloc[-1])
                pct = 0.0
            else:
                current, pct = 0.0, 0.0
            
            vitals[key] = {
                "value": f"{current:,.2f}",
                "delta": f"{'+' if pct >= 0 else ''}{pct:.2f}%"
            }
        except Exception:
            vitals[key] = {"value": "—", "delta": "0.00%"}
    return vitals

def fetch_feed(url, max_items=3):
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "No details available.")).strip()
            # Clean summary tags if any
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
    
    # Real-time RSS feeds
    india_news = fetch_feed("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", 3)
    us_news = fetch_feed("https://finance.yahoo.com/news/rssindex", 3)
    global_news = fetch_feed("https://www.cnbc.com/id/100003114/device/rss/rss.html", 3)

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
