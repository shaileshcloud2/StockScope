import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
from utils.nse500_analyzer import calculate_rsi

def detect_cup_and_handle(df, window=20):
    if len(df) < 60:
        return False, "Insufficient data"
        
    prices = df["Close"].values
    high_52w = np.max(prices)
    current_price = prices[-1]
    
    if current_price < high_52w * 0.98:
        return False, "Not near high"
        
    recent_high_idx = np.argmax(prices[:-10])
    cup_bottom_idx = np.argmin(prices[recent_high_idx:]) + recent_high_idx
    
    if cup_bottom_idx <= recent_high_idx or cup_bottom_idx >= len(prices) - 5:
        return False, "Pattern structure not found"
        
    recovery_high = np.max(prices[cup_bottom_idx:])
    if recovery_high < prices[recent_high_idx] * 0.9:
        return False, "Recovery incomplete"
        
    handle_prices = prices[-10:]
    handle_max = np.max(handle_prices)
    if handle_max > prices[recent_high_idx] * 1.05:
         return False, "Breakout already occurred or too high"
         
    return True, "Potential Cup & Handle forming near high"

def generate_market_analysis_report():
    symbols = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LTIM.NS",
        "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", "ADANIENT.NS"
    ]
    
    report_data = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1y", interval="1wk")
            if df.empty or len(df) < 20: continue
            
            current_price = df["Close"].iloc[-1]
            high_52w = df["High"].max()
            
            if current_price >= high_52w * 0.98:
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
                        "Suggestion": "BUY on Breakout",
                        "Reason": reason,
                        "df": df
                    })
        except Exception:
            continue
            
    return pd.DataFrame(report_data)

def render_pattern_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"])])
    
    fig.update_layout(
        title=f"{symbol} Pattern Analysis",
        yaxis_title="Price",
        template="plotly_dark",
        xaxis_rangeslider_visible=False
    )
    return fig
