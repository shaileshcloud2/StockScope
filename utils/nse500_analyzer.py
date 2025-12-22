import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import numpy as np

NSE500_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "WIPRO.NS", "AXISBANK.NS",
    "KOTAKBANK.NS", "HINDUNILVR.NS", "MARUTI.NS", "TATAMOTORS.NS",
    "M&M.NS", "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
    "BIOCON.NS", "LUPIN.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS",
    "VEDL.NS", "ULTRACEMCO.NS", "SHREECEM.NS", "GRASIM.NS", "ACC.NS",
    "AMBUJACEM.NS", "POWERGRID.NS", "NTPC.NS", "TATAPOWER.NS", "LT.NS",
    "ADANIPORTS.NS", "INDIGO.NS", "DMART.NS", "TRENT.NS", "DLF.NS",
    "SBILIFE.NS", "ICICIPRULI.NS", "HDFCLIFE.NS", "NESTLEIND.NS",
    "BRITANNIA.NS", "DABUR.NS", "GODREJCP.NS", "HEROMOTOCO.NS",
    "BAJAJ-AUTO.NS", "EICHERMOT.NS", "HCLTECH.NS", "TECHM.NS", "LTI.NS",
    "ONGC.NS", "IOC.NS", "BPCL.NS", "HPCL.NS", "COALINDIA.NS",
    "NATIONALUM.NS", "INDUSIND.NS", "BANDHANBNK.NS", "SPICEJET.NS",
    "GODREJPROP.NS", "ADANIPOWER.NS", "IDEA.NS"
]

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index"""
    if len(data) < period:
        return None
    
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def detect_recent_cross(data, days=7):
    """Detect if stock had Golden/Death cross in past N days"""
    if len(data) < 200:
        return None, None
    
    df = data.copy()
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    df['MA_200'] = df['Close'].rolling(window=200).mean()
    
    df['Golden_Cross'] = (df['MA_50'] > df['MA_200']) & (df['MA_50'].shift(1) <= df['MA_200'].shift(1))
    df['Death_Cross'] = (df['MA_50'] < df['MA_200']) & (df['MA_50'].shift(1) >= df['MA_200'].shift(1))
    
    recent_data = df.tail(days)
    
    golden_crosses = recent_data[recent_data['Golden_Cross'] == True]
    death_crosses = recent_data[recent_data['Death_Cross'] == True]
    
    cross_info = None
    cross_type = None
    cross_date = None
    cross_price = None
    
    if not golden_crosses.empty:
        latest_cross = golden_crosses.iloc[-1]
        cross_info = latest_cross
        cross_type = 'Golden Cross'
        cross_date = latest_cross.name
        cross_price = latest_cross['Close']
    elif not death_crosses.empty:
        latest_cross = death_crosses.iloc[-1]
        cross_info = latest_cross
        cross_type = 'Death Cross'
        cross_date = latest_cross.name
        cross_price = latest_cross['Close']
    
    return cross_type, cross_date, cross_price

def get_recommendation(rsi, roi, cross_type):
    """Get buy/hold/sell recommendation based on metrics"""
    if cross_type == 'Golden Cross':
        if rsi > 70:
            return 'HOLD', 'Overbought - Wait for pullback'
        elif rsi > 50:
            return 'BUY', 'Strong uptrend with good momentum'
        else:
            return 'BUY', 'Golden cross with rising momentum'
    elif cross_type == 'Death Cross':
        if rsi < 30:
            return 'SELL', 'Oversold - Strong downtrend'
        elif rsi < 50:
            return 'SELL', 'Death cross with bearish momentum'
        else:
            return 'HOLD', 'Watch for further decline'
    else:
        if roi > 10:
            return 'HOLD', 'Strong performer - Monitor'
        elif roi > 0:
            return 'HOLD', 'Stable performance'
        else:
            return 'SELL', 'Negative trend'

@st.cache_data(ttl=3600)
def analyze_nse500_crosses():
    """Analyze NSE 500 stocks for Golden/Death cross in past week"""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_stocks = len(NSE500_STOCKS)
    
    for idx, symbol in enumerate(NSE500_STOCKS):
        try:
            status_text.text(f"Analyzing {symbol}... ({idx+1}/{total_stocks})")
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1y')
            
            if data.empty or len(data) < 200:
                continue
            
            # Detect cross
            cross_type, cross_date, cross_price = detect_recent_cross(data, days=7)
            
            if cross_type is None:
                continue
            
            # Get current price
            current_price = data['Close'].iloc[-1]
            
            # Calculate metrics
            rsi = calculate_rsi(data)
            roi = ((current_price - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
            
            # Get PE ratio
            pe_ratio = ticker.info.get('trailingPE', 'N/A')
            
            # Calculate % change since cross
            pct_change = ((current_price - cross_price) / cross_price) * 100
            
            # Get recommendation
            recommendation, reason = get_recommendation(rsi, roi, cross_type)
            
            # Get stock name
            stock_name = ticker.info.get('longName', symbol.replace('.NS', ''))
            
            results.append({
                'Symbol': symbol.replace('.NS', ''),
                'Company Name': stock_name,
                'Cross Type': cross_type,
                'Cross Date': cross_date.strftime('%Y-%m-%d'),
                'Price at Cross': f"₹{cross_price:.2f}",
                'Current Price': f"₹{current_price:.2f}",
                'Price Change %': f"{pct_change:+.2f}%",
                'RSI': f"{rsi:.2f}" if rsi else "N/A",
                'P/E Ratio': f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else "N/A",
                'ROI %': f"{roi:.2f}%",
                'Recommendation': recommendation,
                'Reason': reason,
                'pct_value': pct_change
            })
            
            progress_bar.progress((idx + 1) / total_stocks)
            
        except Exception as e:
            continue
    
    status_text.empty()
    progress_bar.empty()
    
    if results:
        # Sort by price change
        results.sort(key=lambda x: x['pct_value'], reverse=True)
        # Remove sorting column
        for result in results:
            del result['pct_value']
        
        return pd.DataFrame(results)
    
    return None

def filter_results(df, cross_type=None, recommendation=None):
    """Filter results by cross type or recommendation"""
    if cross_type and cross_type != "All":
        df = df[df['Cross Type'] == cross_type]
    
    if recommendation and recommendation != "All":
        df = df[df['Recommendation'] == recommendation]
    
    return df
