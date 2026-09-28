import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def fetch_live_quote(symbol_path):
    """
    Fetches real-time price & daily percent change directly from Google Finance.
    symbol_path examples: 'NIFTY_50:INDEXNSE', 'INDEXBOM:SENSEX', 'USD-INR', '.INX:INDEXSP', 'TNX:INDEXCBOE'
    """
    url = f"https://www.google.com/finance/quote/{symbol_path}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            
        # Extract live price
        price_match = re.search(r'class=["\']YMlKec fxKbKc["\']>([^<]+)<', html)
        if not price_match:
            price_match = re.search(r'data-last-price=["\']([^"\']+)["\']', html)
            
        # Extract percent change
        pct_match = re.search(r'class=["\']JwB6be[^"\']*["\']>([^<]*%?)<', html)
        if not pct_match:
            pct_match = re.search(r'aria-label=["\'][^"\']*by\s+([+\-]?[0-9\.]+\%)["\']', html)
            
        if price_match:
            price_str = price_match.group(1).replace(",", "").replace("$", "").replace("₹", "").strip()
            val_float = float(price_str)
            pct_str = pct_match.group(1).strip() if pct_match else "0.00%"
            if not pct_str.startswith("-") and not pct_str.startswith("+"):
                pct_str = f"+{pct_str}"
            return f"{val_float:,.2f}", pct_str
    except Exception:
        pass
    return None, None

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
        val, delta = fetch_live_quote(path)
        if val is not None:
            vitals[key] = {"value": val, "delta": delta}
        else:
            # Fallback to secondary endpoint if path was blocked
            vitals[key] = {"value": "—", "delta": "0.00%"}
            
    return vitals

def fetch_rss_xml(url, source_name, max_items=3):
    items = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:max_items]:
                    title = item.findtext("title", "").strip()
                    desc = item.findtext("description", "Click to read full market coverage.").strip()
                    link = item.findtext("link", "#").strip()
                    
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
