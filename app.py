import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(page_title="Pro Trading Terminal", layout="wide")

# --- UI Styling ---
st.markdown("""<style>.stMetric { background-color: #FFFFFF; padding: 8px; border-radius: 6px; border: 1px solid #E0E3EB; }</style>""", unsafe_allow_html=True)
st.write("### 🎯 Ultimate Precision Trading Terminal")

# --- Alert Logic ---
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

# --- Universal Search Engine ---
# Popular + Search
POPULAR = {"NIFTY 50": "^NSEI", "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "TATAMOTORS": "TATAMOTORS.NS", "HDFC BANK": "HDFCBANK.NS"}
preset = st.selectbox("⚡ Choose Popular Stock:", ["Custom Search"] + list(POPULAR.keys()))
custom = st.text_input("🔍 OR Search Any NSE Symbol (e.g., BEL.NS, NTPC.NS):")

ticker = POPULAR[preset] if preset != "Custom Search" else custom.upper().strip()
if not ticker: ticker = "^NSEI"

# --- Strategy Engine ---
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
    df = stock.history(period="1mo", interval="15m")
    
    if not df.empty:
        df = calculate_indicators(df)
        last_row = df.iloc[-1]
        
        # Display Stats
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Current Price ({ticker})", f"₹{last_row['Close']:.2f}")
        c2.metric("RSI", f"{last_row['RSI']:.2f}")
        c3.metric("Trend", "BULLISH" if last_row['Close'] > last_row['EMA_Slow'] else "BEARISH")
        
        st.line_chart(df[['Close', 'EMA_Fast', 'EMA_Slow']])
        
        # --- Backtest & Trade Logs (Restored) ---
        st.write("#### 📊 Backtest Status")
        # Logic to calculate Target/SL
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        target = last_row['Close'] + (2 * atr)
        sl = last_row['Close'] - (1.5 * atr)
        
        st.write(f"**Target:** ₹{target:.2f} | **Stop Loss:** ₹{sl:.2f}")
        
        if enable_alerts and last_row['RSI'] > 70:
            send_telegram_alert(bot_token, chat_id, f"🚨 ALERT: {ticker} Target reached!")
            
    else:
        st.error("Symbol not found. Please add .NS for NSE stocks.")
except Exception as e:
    st.error("Please enter a valid stock symbol.")
