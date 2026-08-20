import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(page_title="High Precision 2x Volume Trading Terminal", layout="wide")

# Custom UI Styling: Clean White Theme, Compact Font, High Readability
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; color: #1E222D; }
    .stMetric { background-color: #FFFFFF; padding: 8px 12px; border-radius: 6px; border: 1px solid #E0E3EB; }
    div[data-testid="stMetricValue"] > div { font-size: 1.15rem !important; }
    div[data-testid="stMetricLabel"] > div { font-size: 0.75rem !important; }
    .stButton > button { width: 100%; padding: 2px 4px; font-size: 11px; height: 26px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

st.write("### 🎯 2x Volume Surge & Multi-Confluence Precision Terminal")

# Session state initialization
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = "^NSEI"

POPULAR_INSTRUMENTS = {
    "NIFTY 50 (Index)": "^NSEI",
    "BANK NIFTY (Index)": "^NSEBANK",
    "FINNIFTY (Index)": "NIFTY_FIN_SERVICE.NS",
    "CRUDE OIL": "CL=F",
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "TATAPOWER": "TATAPOWER.NS",
    "COFORGE": "COFORGE.NS",
    "RELIANCE": "RELIANCE.NS",
    "HDFC BANK": "HDFCBANK.NS"
}

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS",
    "BHARTIARTL.NS", "INFY.NS", "ITC.NS", "TATAMOTORS.NS", "TATAPOWER.NS"
]

# Top Search Bar
search_col1, search_col2 = st.columns([2, 3])

with search_col1:
    preset_choice = st.selectbox(
        "⚡ Quick Instrument Selector:",
        ["Search Custom Symbol..."] + list(POPULAR_INSTRUMENTS.keys()),
        index=1
    )
    if preset_choice != "Search Custom Symbol...":
        st.session_state.selected_ticker = POPULAR_INSTRUMENTS[preset_choice]

with search_col2:
    custom_search = st.text_input(
        "🔍 Universal Search Bar (Enter Symbol e.g. ^NSEI, ^NSEBANK, CL=F, TATAPOWER.NS):",
        value=st.session_state.selected_ticker
    )
    if custom_search and custom_search != st.session_state.selected_ticker:
        st.session_state.selected_ticker = custom_search.strip()

ticker = st.session_state.selected_ticker

# Helper Calculations
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    sig = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

# Scanner Engine with 2x Volume Filter
@st.cache_data(ttl=120)
def scan_market_stocks(stock_list):
    scan_results = []
    for s in stock_list:
        try:
            t = yf.Ticker(s)
            d = t.history(period="1mo", interval="1d")
            if len(d) >= 20:
                c_price = d['Close'].iloc[-1]
                p_price = d['Close'].iloc[-2]
                pct = ((c_price - p_price) / p_price) * 100
                
                ema20 = d['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
                rsi_val = calculate_rsi(d['Close'], 14).iloc[-1]
                atr_val = calculate_atr(d, 14).iloc[-1]
                vol_sma = d['Volume'].rolling(window=20).mean().iloc[-1]
                last_vol = d['Volume'].iloc[-1]
                
                if np.isnan(atr_val):
                    atr_val = c_price * 0.015
                
                is_vol_surge = last_vol >= (vol_sma * 1.5) if vol_sma > 0 else True
                
                if c_price > ema20 and rsi_val >= 55 and is_vol_surge:
                    action = "🟢 BUY (CALL)"
                    tgt = c_price + (2.0 * atr_val)
                    sl = c_price - (1.5 * atr_val)
                elif c_price < ema20 and rsi_val <= 45 and is_vol_surge:
                    action = "🔴 SELL (PUT)"
                    tgt = c_price - (2.0 * atr_val)
                    sl = c_price + (1.5 * atr_val)
                else:
                    action = "⚪ HOLD"
                    tgt = c_price
                    sl = c_price
                    
                clean_symbol = s.replace(".NS", "")
                scan_results.append({
                    "Symbol": clean_symbol,
                    "Ticker": s,
                    "Price (₹)": f"{c_price:.2f}",
                    "Change": pct,
                    "Change (%)": f"{pct:+.2f}%",
                    "Signal": action,
                    "Target (₹)": f"{tgt:.2f}",
                    "SL (₹)": f"{sl:.2f}"
                })
        except:
            continue
    return pd.DataFrame(scan_results)

market_df = scan_market_stocks(WATCHLIST)

# --- Top 5 Gainers & Losers Tables ---
if not market_df.empty:
    top_gainers = market_df.sort_values(by="Change", ascending=False).head(5).reset_index(drop=True)
    top_losers = market_df.sort_values(by="Change", ascending=True).head(5).reset_index(drop=True)
    
    col_gain, col_loss = st.columns(2)
    with col_gain:
        st.write("##### 🚀 Top 5 Gainers")
        st.dataframe(top_gainers[["Symbol", "Price (₹)", "Change (%)", "Signal", "Target (₹)", "SL (₹)"]], hide_index=True, use_container_width=True)
        btn_cols_g = st.columns(5)
        for i, r in top_gainers.iterrows():
            if btn_cols_g[i].button(f"📊 {r['Symbol']}", key=f"btn_g_{r['Symbol']}"):
                st.session_state.selected_ticker = r['Ticker']
                
    with col_loss:
        st.write("##### 🔻 Top 5 Losers")
        st.dataframe(top_losers[["Symbol", "Price (₹)", "Change (%)", "Signal", "Target (₹)", "SL (₹)"]], hide_index=True, use_container_width=True)
        btn_cols_l = st.columns(5)
        for i, r in top_losers.iterrows():
            if btn_cols_l[i].button(f"📊 {r['Symbol']}", key=f"btn_l_{r['Symbol']}"):
                st.session_state.selected_ticker = r['Ticker']

st.markdown("---")

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Strategy & Volume Controls")
timeframe = st.sidebar.selectbox("Timeframe (5m/15m recommended):", ["5m", "15m", "1h", "1d"], index=1)
period_map = {"5m": "5d", "15m": "1mo", "1h": "3mo", "1d": "1y"}
period = period_map[timeframe]

volume_multiplier = st.sidebar.slider("Volume Surge Multiplier (2x Standard):", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
ema_fast = st.sidebar.number_input("Fast EMA", value=20)
ema_mid = st.sidebar.number_input("Mid EMA", value=50)
ema_slow = st.sidebar.number_input("Trend Filter (Slow EMA 200)", value=200)

# --- Chart & High Precision Backtest Engine ---
if ticker:
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=timeframe)
    
    if not df.empty and len(df) > 50:
        df = df.reset_index()
        
        if 'Datetime' in df.columns:
            df['Datetime_IST'] = pd.to_datetime(df['Datetime']).dt.tz_convert('Asia/Kolkata')
            df['display_time'] = df['Datetime_IST'].dt.strftime('%d-%b-%Y %I:%M %p')
            df['chart_time'] = df['Datetime'].apply(lambda x: int(x.timestamp()))
        elif 'Date' in df.columns:
            df['Datetime_IST'] = pd.to_datetime(df['Date'])
            df['display_time'] = df['Datetime_IST'].dt.strftime('%d-%b-%Y')
            df['chart_time'] = df['Datetime_IST'].dt.strftime('%Y-%m-%d')
            
        # Indicator Calculations
        df['EMA_Fast'] = df['Close'].ewm(span=ema_fast, adjust=False).mean()
        df['EMA_Mid'] = df['Close'].ewm(span=ema_mid, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=ema_slow, adjust=False).mean()
        df['RSI'] = calculate_rsi(df['Close'], 14)
        df['MACD'], df['Signal_Line'] = calculate_macd(df['Close'])
        df['ATR'] = calculate_atr(df, 14)
        df['Vol_SMA'] = df['Volume'].rolling(window=20).mean()
        
        # 2x Volume Filter Check (Adaptive for Indices where volume may be 0)
        has_volume = (df['Volume'] > 0).any()
        if has_volume:
            volume_condition = df['Volume'] >= (df['Vol_SMA'] * volume_multiplier)
        else:
            # For Spot Index without volume data, use Candle Range Momentum as surrogate
            candle_range = df['High'] - df['Low']
            avg_range = candle_range.rolling(window=20).mean()
            volume_condition = candle_range >= (avg_range * 1.5)
        
        # Multi-Confluence Strict Signal Rules
        call_cond = (df['Close'] > df['EMA_Fast']) & (df['EMA_Fast'] > df['EMA_Mid']) & \
                    (df['Close'] > df['EMA_Slow']) & (df['MACD'] > df['Signal_Line']) & \
                    (df['RSI'] >= 52) & (df['RSI'] <= 70) & volume_condition
                    
        put_cond = (df['Close'] < df['EMA_Fast']) & (df['EMA_Fast'] < df['EMA_Mid']) & \
                   (df['Close'] < df['EMA_Slow']) & (df['MACD'] < df['Signal_Line']) & \
                   (df['RSI'] <= 48) & (df['RSI'] >= 30) & volume_condition
        
        signals = []
        last_signal = 0
        for c, p in zip(call_cond, put_cond):
            if c and last_signal != 1:
                signals.append(1)
                last_signal = 1
            elif p and last_signal != -1:
                signals.append(-1)
                last_signal = -1
            else:
                signals.append(0)
        df['Signal'] = signals
        
        # Format Data for Lightweight Charts
        candles = []
        ema_fast_data = []
        ema_mid_data = []
        ema_slow_data = []
        markers = []
        
        for idx, row in df.iterrows():
            candles.append({
                "time": row['chart_time'], "open": float(row['Open']),
                "high": float(row['High']), "low": float(row['Low']), "close": float(row['Close'])
            })
            if not np.isnan(row['EMA_Fast']):
                ema_fast_data.append({"time": row['chart_time'], "value": float(row['EMA_Fast'])})
            if not np.isnan(row['EMA_Mid']):
                ema_mid_data.append({"time": row['chart_time'], "value": float(row['EMA_Mid'])})
            if not np.isnan(row['EMA_Slow']):
                ema_slow_data.append({"time": row['chart_time'], "value": float(row['EMA_Slow'])})
            
            if row['Signal'] == 1:
                markers.append({"time": row['chart_time'], "position": "belowBar", "color": "#089981", "shape": "arrowUp", "text": "🟢 2x VOL CALL"})
            elif row['Signal'] == -1:
                markers.append({"time": row['chart_time'], "position": "aboveBar", "color": "#F23645", "shape": "arrowDown", "text": "🔴 2x VOL PUT"})

        chartOptions = {
            "layout": {"textColor": "#131722", "background": {"type": "solid", "color": "#FFFFFF"}},
            "grid": {"vertLines": {"color": "#F0F3FA"}, "horzLines": {"color": "#F0F3FA"}},
            "crosshair": {"mode": 0},
            "priceScale": {"borderColor": "#D1D4DC", "autoScale": True, "mode": 0},
            "timeScale": {"borderColor": "#D1D4DC", "timeVisible": True, "secondsVisible": False}
        }
        
        series = [
            {
                "type": "Candlestick", "data": candles,
                "options": {"upColor": "#089981", "downColor": "#F23645", "borderUpColor": "#089981", "borderDownColor": "#F23645", "wickUpColor": "#089981", "wickDownColor": "#F23645"},
                "markers": markers
            },
            {"type": "Line", "data": ema_fast_data, "options": {"color": "#2962FF", "lineWidth": 2, "title": f"EMA {ema_fast}"}},
            {"type": "Line", "data": ema_mid_data, "options": {"color": "#AB47BC", "lineWidth": 2, "title": f"EMA {ema_mid}"}},
            {"type": "Line", "data": ema_slow_data, "options": {"color": "#E65100", "lineWidth": 2, "title": f"EMA {ema_slow} (Trend)"}}
        ]
        
        last_row = df.iloc[-1]
        last_price = last_row['Close']
        strike_step = 50 if "^NSEI" in ticker else (100 if "^NSEBANK" in ticker else 10)
        atm_strike = round(last_price / strike_step) * strike_step
        
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        col1.metric("Active Instrument", ticker)
        col2.metric("Spot Price", f"₹{last_price:.2f}" if ".NS" in ticker or "^" in ticker else f"${last_price:.2f}")
        col3.metric("Suggested ATM Strike", f"{atm_strike}")
        col4.metric("RSI (14)", f"{last_row['RSI']:.2f}")
        col5.metric("Market Trend", "STRONG BULLISH 🚀" if last_price > last_row['EMA_Slow'] else "STRONG BEARISH 🔻")
        
        renderLightweightCharts([{"chart": chartOptions, "series": series}], f"chart_{ticker}")
        
        # Backtest Accuracy Verification Engine (1:2 Risk-to-Reward)
        trade_logs = []
        target_hits = 0
        sl_hits = 0
        signal_indices = df[df['Signal'] != 0].index.tolist()
        
        for s_idx in signal_indices:
            row = df.loc[s_idx]
            sig_type = row['Signal']
            entry_price = row['Close']
            atr_val = row['ATR'] if not np.isnan(row['ATR']) else (entry_price * 0.004)
            
            if sig_type == 1:
                sl_price = entry_price - (1.2 * atr_val)
                tgt_price = entry_price + (2.4 * atr_val)
            else:
                sl_price = entry_price + (1.2 * atr_val)
                tgt_price = entry_price - (2.4 * atr_val)
                
            status = "OPEN ⏳"
            for future_idx in range(s_idx + 1, len(df)):
                future_row = df.loc[future_idx]
                f_high = future_row['High']
                f_low = future_row['Low']
                
                if sig_type == 1:
                    if f_high >= tgt_price:
                        status = "TARGET HIT 🎯"
                        target_hits += 1
                        break
                    elif f_low <= sl_price:
                        status = "SL HIT ❌"
                        sl_hits += 1
                        break
                elif sig_type == -1:
                    if f_low <= tgt_price:
                        status = "TARGET HIT 🎯"
                        target_hits += 1
                        break
                    elif f_high >= sl_price:
                        status = "SL HIT ❌"
                        sl_hits += 1
                        break
                        
            trade_logs.append({
                "Date & Time (IST)": row['display_time'],
                "Signal": "🟢 2x VOL CALL" if sig_type == 1 else "🔴 2x VOL PUT",
                "Entry Price": f"{entry_price:.2f}",
                "Stop Loss": f"{sl_price:.2f}",
                "Target (1:2)": f"{tgt_price:.2f}",
                "Status": status
            })
            
        completed = target_hits + sl_hits
        accuracy = (target_hits / completed * 100) if completed > 0 else 0.0
        
        st.write("#### 📊 Strategy Backtest & Accuracy Score")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Signals", len(trade_logs))
        m2.metric("Target Hit", f"{target_hits} 🎯")
        m3.metric("SL Hit", f"{sl_hits} ❌")
        m4.metric("Win Rate", f"{accuracy:.1f}%")
        
        if trade_logs:
            with st.expander("View Signal & Trade History", expanded=True):
                st.dataframe(pd.DataFrame(trade_logs).iloc[::-1], use_container_width=True)
    else:
        st.warning("Insufficient historical data. Please switch timeframe or verify symbol.")