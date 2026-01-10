import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils.nse500_analyzer import calculate_rsi

def detect_cup_and_handle(df):
    if len(df) < 40:
        return False, "Insufficient data"
        
    prices = df["Close"].values
    all_time_high = np.max(prices)
    current_price = prices[-1]
    
    # Check if we are near lifetime high (between 2% below to 5% above)
    lower_bound = all_time_high * 0.98
    upper_bound = all_time_high * 1.05
    
    if not (current_price >= lower_bound and current_price <= upper_bound):
        return False, f"Price {current_price:.2f} outside range [{lower_bound:.2f}, {upper_bound:.2f}]"
        
    # Heuristic-based detection for long-term patterns
    recent_prices = prices[:-8]
    if len(recent_prices) == 0: return False, "Data too short"
    
    prev_high_idx = np.argmax(recent_prices)
    cup_bottom_idx = np.argmin(prices[prev_high_idx:]) + prev_high_idx
    
    if cup_bottom_idx <= prev_high_idx or cup_bottom_idx >= len(prices) - 4:
        return False, "Structure not matching cup & handle"
        
    recovery_high = np.max(prices[cup_bottom_idx:])
    if recovery_high < prices[prev_high_idx] * 0.85:
        return False, "Recovery from cup bottom insufficient"
        
    # Handle check: Most recent prices (last few weeks/months)
    handle_prices = prices[-8:]
    handle_max = np.max(handle_prices)
    if handle_max > prices[prev_high_idx] * 1.15:
         return False, "Handle level too high"
         
    return True, "Long-term Cup & Handle pattern detected near Lifetime High range"

def generate_market_analysis_report():
    symbols = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LTIM.NS",
        "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", "ADANIENT.NS",
        "SUNPHARMA.NS", "ULTRACEMCO.NS", "WIPRO.NS", "AXISBANK.NS", "HCLTECH.NS"
    ]
    
    report_data = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="max", interval="1mo")
            if df.empty or len(df) < 48:
                df = ticker.history(period="max", interval="1wk")
                if df.empty or len(df) < 100: continue
            
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            current_price = df["Close"].iloc[-1]
            all_time_high = df["High"].max()
            
            # Updated range: 2% below to 5% above Lifetime High
            if current_price >= (all_time_high * 0.98) and current_price <= (all_time_high * 1.05):
                is_pattern, reason = detect_cup_and_handle(df)
                if is_pattern:
                    info = ticker.info
                    rsi_series = calculate_rsi(df["Close"])
                    rsi = rsi_series.iloc[-1] if not rsi_series.empty else 0
                    
                    vol_val = df["Volume"].iloc[-1]
                    formatted_vol = "{:,}".format(int(vol_val))
                    
                    report_data.append({
                        "Symbol": symbol,
                        "Name": info.get("longName", symbol),
                        "Current Price": f"₹{current_price:.2f}",
                        "RSI": f"{rsi:.1f}",
                        "Volume": formatted_vol,
                        "PE": info.get("trailingPE", "N/A"),
                        "Suggestion": "Breakout Momentum BUY",
                        "Reason": reason,
                        "df": df
                    })
        except Exception:
            continue
            
    return pd.DataFrame(report_data)

def render_pattern_chart(df, symbol):
    plot_df = df.tail(120)
    fig = go.Figure(data=[go.Candlestick(x=plot_df.index,
                open=plot_df["Open"],
                high=plot_df["High"],
                low=plot_df["Low"],
                close=plot_df["Close"])])
    
    fig.update_layout(
        title=f"{symbol} Long-term Pattern Analysis",
        yaxis_title="Price",
        template="plotly_dark",
        xaxis_rangeslider_visible=False
    )
    return fig
