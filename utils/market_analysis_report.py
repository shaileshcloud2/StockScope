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
    
    # Check if we are near lifetime high (within 2