import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go

def generate_ath_breakout_report():
    """
    Generate report for stocks at All-Time High Breakout.
    Criteria:
    - Current price * 1.1 > High price all time (within 10% of ATH or above)
    - Current price > 10 rupees
    - Volume > 10000
    - Market Capitalization > 500Cr
    - Price > 2% above 52W High
    """
    # Expanded list for better coverage
    symbols = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LTIM.NS",
        "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS", "ADANIENT.NS",
        "SUNPHARMA.NS", "ULTRACEMCO.NS", "WIPRO.NS", "AXISBANK.NS", "HCLTECH.NS",
        "TATASTEEL.NS", "M&M.NS", "POWERGRID.NS", "NTPC.NS", "ONGC.NS", "ADANIPORTS.NS"
    ]
    
    report_data = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Market Cap > 500Cr (Convert to INR Cr from absolute if needed)
            mcap = info.get('marketCap', 0)
            if mcap < 5000000000: continue # 500 Cr = 5e9
            
            # Current price > 10
            # Use 'regularMarketPrice' if available, otherwise fetch history
            df_recent = ticker.history(period="5d")
            if df_recent.empty: continue
            current_price = df_recent["Close"].iloc[-1]
            if current_price <= 10: continue
            
            # Volume > 10000
            volume = df_recent["Volume"].iloc[-1]
            if volume <= 10000: continue
            
            # Fetch Max data for true ATH
            df_max = ticker.history(period="max")
            if df_max.empty: continue
            all_time_high = df_max["High"].max()
            
            # Fetch 52W High
            df_1y = ticker.history(period="1y")
            high_52w = df_1y["High"].max() if not df_1y.empty else all_time_high
            
            # Criteria: Current price * 1.1 > ATH AND Current price > 1.02 * 52W High
            if (current_price * 1.1 > all_time_high) and (current_price > high_52w * 1.02):
                report_data.append({
                    "Symbol": symbol,
                    "Name": info.get("longName", symbol),
                    "Current Price": f"₹{current_price:.2f}",
                    "52W High": f"₹{high_52w:.2f}",
                    "All-Time High": f"₹{all_time_high:.2f}",
                    "Market Cap (Cr)": f"{mcap/10000000:,.0f}",
                    "Volume": f"{volume:,}",
                    "PE": info.get("trailingPE", "N/A"),
                    "Suggestion": "ATH Breakout BUY",
                    "Reason": "Breaking out above multi-year resistance with strong volume",
                    "df": df_max.tail(250)
                })
        except Exception:
            continue
            
    return pd.DataFrame(report_data)

def render_ath_chart(df, symbol):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"])])
    
    fig.update_layout(
        title=f"{symbol} ATH Breakout Analysis",
        yaxis_title="Price",
        template="plotly_dark",
        xaxis_rangeslider_visible=False
    )
    return fig
