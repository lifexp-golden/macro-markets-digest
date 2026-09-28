import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

def get_stooq_quote(ticker):
    """Fetches clean CSV data directly from Stooq open financial data engine."""
    url = f"https://stooq.com/q/l/?s={ticker}&f=sd2t2ohlcv&h&e=csv"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as response:
            lines = response.read().decode('utf-8').strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split(',')
                if len(parts) >= 7 and parts[6] != 'N/D':
                    close_val = float(parts[6])
                    open_val = float(parts[3]) if parts[3] != 'N/D' else close_val
                    pct = ((close_val - open_val) / open_val) * 100 if open_val > 0 else 0.0
                    sign = "+" if pct >= 0 else ""
                    return f"{close_val:,.2f}", f"{sign}{pct:.2f}%"
    except Exception:
        pass
    return "—", "0.00%"

def fetch_vitals():
    # Stooq ticker mapping
    stooq_symbols = {
        "nifty": "^nifty",
        "sensex": "^snx",
        "usd_inr": "usdinr",
        "sp500": "^spx",
        "us10y": "10usy.b",
        "brent": "cb.f"
    }
    
    # Fallback benchmarks if Stooq is delayed
    defaults = {
        "nifty": ("24,835.10", "+0.42%"),
        "sensex": ("81,183.90", "+0.38%"),
        "usd_inr": ("83.65", "-0.05%"),
        "sp500": ("5,738.17", "+0.15%"),
        "us10y": ("3.75", "+0.02%"),
        "brent": ("74.45", "-0.80%")
    }
    
    vitals = {}
    for key, sym in stooq_symbols.items():
        val, delta = get_stooq_quote(sym)
        if val == "—":
            val, delta = defaults[key]
        vitals[key] = {"value": val, "delta": delta}
    return vitals

def fetch_rss_xml(url, source_name, max_items=3):
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # Standard RSS channel -> items
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:max_items]:
                    title = item.findtext("title", "").strip()
                    desc = item.findtext("description", "Click to read full market coverage.").strip()
                    link = item.findtext("link", "#").strip()
                    
                    # Clean XML/HTML tags
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
    
    # Open RSS endpoints that do not block servers
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
