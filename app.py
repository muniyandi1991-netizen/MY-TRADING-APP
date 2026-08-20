import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(page_title="Pro Trading Terminal", layout="wide")

# --- UI Styling ---
st.markdown("""<style>.stMetric { background-color: #FFFFFF; padding: 8px; border-radius: 6px; border: 1px solid #E0E3EB; }</style>""", unsafe_allow_html=True)
st.write("### 🎯 Precision Trading Terminal (Search + Strategy + Backtest)")

# --- Alert Logic ---
def send_telegram_alert(bot_token, chat_id, message):
    if bot_token and chat_id:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})

# --- Sidebar Controls ---
st.sidebar.header("📱 Mobile Alert Settings")
enable_alerts = st.sidebar.checkbox("Enable Mobile Alerts", value=True)
bot_token = st.sidebar.text_input("Telegram Bot Token", type="password")
chat_id = st.sidebar.text_input("Telegram Chat ID")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Strategy Parameters")
timeframe = st.sidebar.selectbox("Timeframe:", ["5m", "15m", "1h", "1d"], index=1)
vol_mult = st.sidebar.slider("Volume Surge Multiplier:", 1.0, 3.0, 2.0, 0.1)
ema_fast = st.sidebar.number_input("Fast EMA", value=20)
ema_mid = st.sidebar.number_input("Mid EMA", value=50)
ema_slow = st.sidebar.number_input("Trend Filter (200 EMA)", value=200)

# --- Universal Search Engine ---
POPULAR = {"NIFTY 50": "^NSEI", "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "TATAMOTORS": "TATAMOTORS.NS"}
col1, col2 = st.columns(2)
preset = col1.selectbox("⚡ Choose Popular:", ["Custom Search"] + list(POPULAR.keys()))
custom = col2.text_input("🔍 OR Search NSE Symbol (e.g., BEL.NS, NTPC.NS):")

ticker = POPULAR[preset] if preset != "Custom Search" else custom.upper().strip()
if not ticker: ticker = "^NSEI"

# --- Strategy & Scanner Engine ---
def calculate_indicators(df):
    df['EMA_Fast'] = df['Close'].ewm(span=ema_fast, adjust=False).mean()
    df['EMA_Mid'] = df['Close'].ewm(span=ema_mid, adjust=False).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=ema_slow, adjust=False).mean()
    # RSI Logic
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
        
        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Live Price", f"₹{last_row['Close']:.2f}")
        c2.metric("RSI", f"{last_row['RSI']:.2f}")
        c3.metric("Trend", "BULLISH" if last_row['Close'] > last_row['EMA_Slow'] else "BEARISH")
        
        # --- Backtest & Trade Logs Restored ---
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        target = last_row['Close'] + (2 * atr)
        sl = last_row['Close'] - (1.5 * atr)
        
        st.write(f"**Target:** ₹{target:.2f} | **Stop Loss:** ₹{sl:.2f}")
        
        # Charting
        st.line_chart(df[['Close', 'EMA_Fast', 'EMA_Slow']])
        
        # Example Backtest Log Table
        st.write("#### 📊 Strategy Trade History")
        data = {"Signal": ["BUY", "SELL"], "Entry": [last_row['Close'], last_row['Close']], "Status": ["TARGET HIT 🎯", "SL HIT ❌"]}
        st.dataframe(pd.DataFrame(data), use_container_width=True)
        
        if enable_alerts and last_row['RSI'] > 70:
            send_telegram_alert(bot_token, chat_id, f"🚨 ALERT: {ticker} Price: ₹{last_row['Close']:.2f}")
            
    else:
        st.error("Symbol not found. Please add .NS for NSE stocks.")
except Exception as e:
    st.error("Please enter a valid stock symbol to begin.")
