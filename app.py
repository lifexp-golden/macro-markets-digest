import streamlit as st
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import generate_digest

st.set_page_config(page_title="Macro & Markets Digest", layout="wide", page_icon="📊")

# Custom Dark Theme Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .news-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Header & Refresh Controls
head_col1, head_col2 = st.columns([5, 1])
with head_col1:
    st.title("📊 Macro & Markets Digest")
with head_col2:
    st.write("")
    if st.button("🔄 Refresh Data"):
        with st.spinner("Fetching live market data..."):
            try:
                fresh_data = generate_digest.main()
                st.session_state["cached_data"] = fresh_data
                st.rerun()
            except Exception as e:
                st.error(f"Execution Error: {e}")

# Load Initial Data
if "cached_data" not in st.session_state:
    try:
        if os.path.exists("today.json"):
            with open("today.json", "r", encoding="utf-8") as f:
                st.session_state["cached_data"] = json.load(f)
        else:
            st.session_state["cached_data"] = generate_digest.main()
    except Exception as e:
        st.session_state["cached_data"] = generate_digest.main()

data = st.session_state.get("cached_data", {})
vitals = data.get("vitals", {})

st.caption(f"Last Refreshed: {data.get('date', datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST'))} • Executive Terminal View")

# Market Vitals Grid
st.subheader("Market Vitals")
cols = st.columns(6)
ticker_items = [
    ("Nifty 50", vitals.get("nifty", {"value": "—", "delta": "0.00%"})),
    ("Sensex", vitals.get("sensex", {"value": "—", "delta": "0.00%"})),
    ("USD / INR", vitals.get("usd_inr", {"value": "—", "delta": "0.00%"})),
    ("S&P 500", vitals.get("sp500", {"value": "—", "delta": "0.00%"})),
    ("US 10Y Yield", vitals.get("us10y", {"value": "—", "delta": "0.00%"})),
    ("Brent Crude", vitals.get("brent", {"value": "—", "delta": "0.00%"}))
]

for col, (label, val_dict) in zip(cols, ticker_items):
    with col:
        st.metric(label=label, value=val_dict.get("value", "—"), delta=val_dict.get("delta", "0.00%"))

st.markdown("---")

# The 60-Second Macro Pulse
st.subheader("The 60-Second Macro Pulse")
nifty_val = vitals.get("nifty", {}).get("value", "—")
nifty_delta = vitals.get("nifty", {}).get("delta", "0.00%")
sp_val = vitals.get("sp500", {}).get("value", "—")
sp_delta = vitals.get("sp500", {}).get("delta", "0.00%")
brent_val = vitals.get("brent", {}).get("value", "—")

st.markdown(f"""
- **Equity Momentum:** Nifty 50 at {nifty_val} ({nifty_delta}); S&P 500 at {sp_val} ({sp_delta}).
- **Energy & Commodities:** Brent Crude trading at {brent_val} per barrel.
- **Macro Focus:** Tracking monetary policy prints, bond yield trajectories, and global trade flows.
""")

st.markdown("---")

# News Section
feed_col1, feed_col2, feed_col3 = st.columns(3)

def render_news_column(col, header, items):
    with col:
        st.subheader(header)
        for item in items:
            st.markdown(f"""
            <div class="news-card">
                <b><a href="{item.get('link', '#')}" target="_blank" style="text-decoration:none; color:#58a6ff;">{item.get('title', 'Market Update')}</a></b><br>
                <small style="color:#8b949e;">{item.get('summary', '')}</small><br>
                <span style="font-size:11px; color:#58a6ff;">Source: {item.get('source', 'Wire')}</span>
            </div>
            """, unsafe_allow_html=True)

render_news_column(feed_col1, "🇮🇳 India: Markets & Economy", data.get("india", []))
render_news_column(feed_col2, "🇺🇸 US: Wall St & Fed", data.get("us", []))
render_news_column(feed_col3, "🌐 Global Themes & Macro", data.get("global", []))
