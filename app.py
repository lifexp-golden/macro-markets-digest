import streamlit as st
import json
import os
import subprocess
from datetime import datetime
import generate_digest

st.set_page_config(
    page_title="Macro & Markets Digest",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 95%; }
        .story-box {
            background-color: #1e222d;
            border-left: 3px solid #38bdf8;
            padding: 12px 14px;
            border-radius: 6px;
            margin-bottom: 12px;
        }
        .story-title { font-size: 14px; font-weight: 600; color: #f8fafc; margin-bottom: 4px; }
        .story-fact { font-size: 12px; color: #94a3b8; line-height: 1.4; }
        .story-impact { font-size: 11px; color: #38bdf8; font-weight: 500; margin-top: 4px; }
    </style>
""", unsafe_allow_html=True)

# Top Bar with Refresh Action
header_col1, header_col2 = st.columns([5, 1])

with header_col1:
    st.title("📊 Macro & Markets Digest")

with header_col2:
        st.write("")
        if st.button("🔄 Refresh Data"):
            with st.spinner("Fetching latest market data & wires..."):
                try:
                    import generate_digest
                    if hasattr(generate_digest, "main"):
                        generate_digest.main()
                    elif hasattr(generate_digest, "generate_briefing"):
                        generate_digest.generate_briefing()
                    else:
                        import importlib
                        importlib.reload(generate_digest)
                    st.rerun()
                except Exception as e:
                    st.error(f"Scraper error: {e}")

if not os.path.exists("today.json"):
    st.warning("Data file not found. Generating initial briefing...")
    subprocess.run(["python", "generate_digest.py"])
    st.rerun()

with open("today.json", "r") as f:
    data = json.load(f)

st.caption(f"Last Refreshed: {data.get('date', datetime.today().strftime('%Y-%m-%d %H:%M'))} • Executive Terminal View")

# 1. Market Vitals
st.subheader("Market Vitals")
vitals = data.get("vitals", {})

c1, c2, c3, c4, c5, c6 = st.columns(6)
cards = [
    (c1, "Nifty 50", vitals.get("nifty")),
    (c2, "Sensex", vitals.get("sensex")),
    (c3, "USD / INR", vitals.get("usdinr")),
    (c4, "S&P 500", vitals.get("sp500")),
    (c5, "US 10Y Yield", vitals.get("us10y")),
    (c6, "Brent Crude", vitals.get("brent"))
]

for col, name, item in cards:
    if isinstance(item, dict):
        price = item.get("price", "—")
        change = item.get("change", None)
    elif isinstance(item, str):
        price = item
        change = None
    else:
        price = "—"
        change = None
    col.metric(label=name, value=price, delta=change)

st.divider()

# 2. Macro Pulse
st.subheader("The 60-Second Macro Pulse")
for point in data.get("macro_pulse", []):
    st.markdown(f"• **{point}**")

st.divider()

# 3. Regional Columns
col_in, col_us, col_gl = st.columns(3)

def render_column(stories):
    if not stories:
        st.write("No updates available.")
        return
    for item in stories:
        if isinstance(item, dict):
            headline = item.get("headline", "Market Update")
            fact = item.get("fact", "")
            impact = item.get("impact", "")
        else:
            headline = str(item)
            fact = ""
            impact = ""
            
        st.markdown(f"""
        <div class="story-box">
            <div class="story-title">{headline}</div>
            {"<div class='story-fact'><b>Fact:</b> " + fact + "</div>" if fact else ""}
            {"<div class='story-impact'>" + impact + "</div>" if impact else ""}
        </div>
        """, unsafe_allow_html=True)

with col_in:
    st.subheader("🇮🇳 India: Markets & Economy")
    render_column(data.get("india", []))

with col_us:
    st.subheader("🇺🇸 US: Wall St & Fed")
    render_column(data.get("us", []))

with col_gl:
    st.subheader("🌍 Global Themes & Macro")
    render_column(data.get("global", []))
