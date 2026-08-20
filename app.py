import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(page_title="Universal Trading Terminal", layout="wide")

# --- UI Styling ---
st.markdown("""<style>.stMetric { background-color: #FFFFFF; padding: 8px; border-radius: 6px; border: 1px solid #E0E3EB; }</style>""", unsafe_allow_html=True)
st.write("### 🎯 Precision Terminal: Strategy + Universal Search")

# --- Telegram Alert Function ---
def send_telegram_alert(bot_token, chat_id, message):
    if bot_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=5)
        except: pass

# --- Sidebar ---
st.sidebar.header("📱 Mobile Alert Settings")
enable_alerts = st.sidebar.checkbox("Enable Mobile Alerts", value=True)
bot_token = st.sidebar.text_input("Telegram Bot Token", type="password")
chat_id = st.sidebar.text_input("Telegram Chat ID")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Strategy Parameters")
timeframe = st.sidebar.selectbox("Timeframe:", ["5m", "15m", "1h", "1d"], index=1)
vol_mult = st.sidebar.slider("Volume Surge Multiplier:", 1.0, 3.0, 2.0, 0.1)

# --- NEW: Universal Search Engine ---
# Your watch list + Search bar
WATCHLIST = ["^NSEI", "^NSEBANK", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS"]
custom_search = st.text_input("🔍 Search Any NSE Symbol (e.g., BEL.NS, NTPC.NS):")
ticker = custom_search.upper().strip() if custom_search else "^NSEI"

# --- YOUR ORIGINAL LOGIC ENGINE ---
def calculate_indicators(df):
    df['EMA_Fast'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_Mid'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=200, adjust=False).mean()
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    return df

# Data Fetching
try:
    stock = yf.Ticker(ticker)
    df = stock.history(period="1mo", interval=timeframe)
    if not df.empty:
        df = calculate_indicators(df)
        last_row = df.iloc[-1]
        
        # Display Metrics (The ones you liked)
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Live Price ({ticker})", f"₹{last_row['Close']:.2f}")
        c2.metric("RSI", f"{last_row['RSI']:.2f}")
        c3.metric("Trend", "BULLISH" if last_row['Close'] > last_row['EMA_Slow'] else "BEARISH")
        
        # Original Charting
        st.line_chart(df[['Close', 'EMA_Fast', 'EMA_Slow']])
        
        # Gainers / Losers Placeholder Logic (Restoring your original approach)
        st.write("#### 📊 Strategy Trade History")
        data = {"Symbol": [ticker], "Signal": ["BUY"], "Target": [last_row['Close'] * 1.05], "SL": [last_row['Close'] * 0.98]}
        st.dataframe(pd.DataFrame(data), use_container_width=True)
        
    else:
        st.error("Invalid Symbol. Try adding .NS (e.g., RELIANCE.NS)")
except Exception as e:
    st.error("Enter a stock symbol to begin.")
