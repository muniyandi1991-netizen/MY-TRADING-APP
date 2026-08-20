import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="Pro Trading Terminal", layout="wide")

# --- Styling ---
st.markdown("""<style>.stMetric { background-color: #FFFFFF; padding: 10px; border-radius: 6px; border: 1px solid #E0E3EB; }</style>""", unsafe_allow_html=True)

st.write("### 🎯 Universal Trading Engine (Search Any Stock)")

# --- Sidebar Alerts ---
st.sidebar.header("📱 Mobile Alert Settings")
enable_alerts = st.sidebar.checkbox("Enable Alerts", value=True)
bot_token = st.sidebar.text_input("Telegram Bot Token", type="password")
chat_id = st.sidebar.text_input("Telegram Chat ID")

# --- Search Logic ---
popular_stocks = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS", "HDFC BANK": "HDFCBANK.NS", "SBIN": "SBIN.NS",
    "INFY": "INFY.NS", "ITC": "ITC.NS", "TATAMOTORS": "TATAMOTORS.NS"
}

# 1. Selectbox for popular
choice = st.selectbox("⚡ Choose Popular Stock:", list(popular_stocks.keys()))
# 2. Text input for ANY stock in NSE
search = st.text_input("🔍 OR Search Custom Stock Symbol (e.g. BEL.NS, COFORGE.NS, NTPC.NS):")

ticker = popular_stocks[choice] if not search else search.upper().strip()

# --- Logic & Alerting ---
def send_alert(message):
    if enable_alerts and bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})

# Data Fetching
try:
    stock = yf.Ticker(ticker)
    df = stock.history(period="1mo", interval="15m")
    
    if not df.empty:
        last_price = df['Close'].iloc[-1]
        st.metric(f"Price: {ticker}", f"₹{last_price:.2f}")
        
        # Strategy Logic (Simplified for brevity, integrate your previous logic here)
        st.line_chart(df['Close'])
        
        # Example Alert Trigger
        if enable_alerts and last_price > 0:
             send_alert(f"📊 Dashboard active for {ticker}. Last Price: ₹{last_price:.2f}")
    else:
        st.warning("Symbol not found. Please ensure you add '.NS' for NSE stocks (e.g., RELIANCE.NS).")
except Exception as e:
    st.error(f"Error: {e}")
