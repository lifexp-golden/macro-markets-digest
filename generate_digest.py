import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def fetch_json_quote(ticker):
    """
    Directly queries the Yahoo Finance v8 chart JSON API.
    Zero scraping, no crumb/cookie needed, cloud-safe.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            meta = data["chart"]["result"][0]["meta"]
            
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose", meta.get("previousClose", price))
            
            if price is not None:
                price = float(price)
                if prev_close and float(prev_close) > 0:
                    pct = ((price - float(prev_close)) / float(prev_close)) * 100
                else:
                    pct = 0.0
                sign = "+" if pct >= 0 else ""
                return f"{price:,.2f}", f"{sign}{pct:.2f}%"
    except Exception:
        pass
    return "—", "0.00%"

def fetch_vitals():
    symbols = {
        "nifty": "%5ENSEI",       # ^NSEI (Nifty 50)
        "sensex": "%5EBSESN",     # ^BSESN (Sensex)
        "usd_inr": "INR=X",       # USD / INR
        "sp500": "%5EGSPC",       # ^GSPC (S&P 500)
        "us10y": "%5ETNX",        # ^TNX (US 10Y Yield)
        "brent": "BZ=F"           # Brent Crude
    }
    
    vitals = {}
    for key, sym in symbols.items():
        val, delta = fetch_json_quote(sym)
        vitals[key] = {"value": val, "delta": delta}
    return vitals

def fetch_rss_xml(url, source_name, max_items=3):
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=8) as response:
            root = ET.fromstring(response.read())
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:max_items]:
                    title = item.findtext("title", "").strip()
                    desc = item.findtext("description", "Click to read full market coverage.").strip()
                    link = item.findtext("link", "#").strip()
                    
                    import re
                    desc = re.sub(r'<[^>]+>', '', desc).replace("&nbsp;", " ")
                    if len(desc) > 160:
                        desc = desc[:160] + "..."
                        
                    if title:
                        items.append({
                            "title": title,
                            "summary": desc if desc else "Live macro market briefing.",
                            "link": link,
                            "source": source_name
                        })
    except Exception:
        pass
        
    if not items:
        items = [{
            "title": f"{source_name} Live Dispatch",
            "summary": "Tracking central bank communications, equity flows, and yields.",
            "link": "#",
            "source": source_name
        }]
    return items

def main():
    vitals = fetch_vitals()
    
    india_news = fetch_rss_xml("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "ET Markets")
    us_news = fetch_rss_xml("https://feeds.content.dowjones.io/public/rss/mw_topstories", "MarketWatch")
    global_news = fetch_rss_xml("https://www.cnbc.com/id/100003114/device/rss/rss.html", "CNBC Macro")

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
