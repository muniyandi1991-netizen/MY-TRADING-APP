import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(page_title="Universal High-Precision Trading Terminal", layout="wide")

# Styling
st.markdown("""<style>.stMetric { background-color: #FFFFFF; padding: 8px; border-radius: 6px; border: 1px solid #E0E3EB; }</style>""", unsafe_allow_html=True)
st.write("### 🎯 Precision Trading Terminal (Custom Search + Strategy)")

# --- Telegram Alert Functions ---
def send_telegram_alert(bot_token, chat_id, message):
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})

# --- Sidebar ---
st.sidebar.header("📱 Mobile Alert Settings")
enable_alerts = st.sidebar.checkbox("Enable Mobile Alerts", value=True)
bot_token = st.sidebar.text_input("Telegram Bot Token", type="password")
chat_id = st.sidebar.text_input("Telegram Chat ID")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Strategy Parameters")
timeframe = st.sidebar.selectbox("Timeframe:", ["5m", "15m", "1h", "1d"], index=1)
vol_mult = st.sidebar.slider("Volume Surge Multiplier:", 1.0, 3.0, 2.0, 0.1)

# --- Universal Search Engine ---
# Popular ones
POPULAR = {"NIFTY 50": "^NSEI", "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "TATAMOTORS": "TATAMOTORS.NS"}
preset = st.selectbox("⚡ Choose Popular:", ["Custom Search"] + list(POPULAR.keys()))
custom = st.text_input("🔍 Type any Symbol (e.g., RELIANCE.NS, BEL.NS, NTPC.NS):")

ticker = POPULAR[preset] if preset != "Custom Search" else custom.upper().strip()

if not ticker: ticker = "^NSEI"

# --- Strategy Engine ---
def calculate_indicators(df):
    df['EMA_Fast'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_Mid'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=200, adjust=False).mean()
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
        
        st.metric(f"Live Price: {ticker}", f"₹{last_row['Close']:.2f}")
        
        # Charting
        st.line_chart(df[['Close', 'EMA_Fast', 'EMA_Slow']])
        
        # Strategy Alerts
        if enable_alerts and last_row['RSI'] > 70:
            send_alert(f"🚨 ALERT: {ticker} is Overbought (RSI: {last_row['RSI']:.2f})")
        elif enable_alerts and last_row['RSI'] < 30:
            send_alert(f"🚨 ALERT: {ticker} is Oversold (RSI: {last_row['RSI']:.2f})")
    else:
        st.error("Symbol not found. Please use valid NSE symbol (e.g., RELIANCE.NS).")
except Exception as e:
    st.error("Enter a valid stock symbol to start.")
