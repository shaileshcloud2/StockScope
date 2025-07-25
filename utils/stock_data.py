import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

class StockDataFetcher:
    """Class to handle stock data fetching from Yahoo Finance for Indian stocks."""
    
    def __init__(self):
        self.session = None
    
    def _try_symbol_variations(self, base_symbol, period="6mo"):
        """
        Try different variations of Indian stock symbols.
        NSE symbols end with .NS, BSE symbols end with .BO
        """
        # Clean the base symbol
        base_symbol = base_symbol.upper().strip()
        
        # Remove existing suffixes if present
        if base_symbol.endswith('.NS') or base_symbol.endswith('.BO'):
            base_symbol = base_symbol[:-3]
        
        # Try different variations in order of preference
        variations = [
            f"{base_symbol}.NS",  # NSE first (most common)
            f"{base_symbol}.BO",  # BSE second
            base_symbol,          # Sometimes works without suffix
        ]
        
        for symbol in variations:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)
                
                if not data.empty and len(data) > 5:  # Ensure we have meaningful data
                    return data, symbol
                    
            except Exception as e:
                continue
        
        return None, None
    
    def fetch_stock_data(self, symbol, period="6mo"):
        """
        Fetch stock data for Indian stocks with automatic symbol variation handling.
        
        Args:
            symbol (str): Stock symbol (with or without exchange suffix)
            period (str): Time period for data (1mo, 3mo, 6mo, 1y, 2y, 5y)
        
        Returns:
            pandas.DataFrame: Stock data with OHLCV columns
        """
        try:
            # First try the symbol as provided
            if symbol.endswith('.NS') or symbol.endswith('.BO'):
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)
                
                if not data.empty and len(data) > 5:
                    return self._process_stock_data(data)
            
            # If direct fetch failed or symbol has no suffix, try variations
            data, found_symbol = self._try_symbol_variations(symbol, period)
            
            if data is not None:
                return self._process_stock_data(data)
            else:
                # Try with longer period in case short period has no data
                if period != "1y":
                    data, found_symbol = self._try_symbol_variations(symbol, "1y")
                    if data is not None:
                        # Filter to requested period
                        processed_data = self._process_stock_data(data)
                        if processed_data is not None:
                            return processed_data.tail(self._get_period_days(period))
                
                return None
                
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def _process_stock_data(self, data):
        """
        Process and clean the stock data.
        
        Args:
            data (pandas.DataFrame): Raw stock data from yfinance
            
        Returns:
            pandas.DataFrame: Processed stock data
        """
        if data.empty:
            return None
        
        # Reset index to make Date a column
        data = data.copy()
        
        # Remove timezone info if present
        if hasattr(data.index, 'tz_localize'):
            data.index = data.index.tz_localize(None)
        
        # Ensure we have the required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in data.columns:
                st.error(f"Missing required column: {col}")
                return None
        
        # Round numeric columns to 2 decimal places
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Adj Close']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = data[col].round(2)
        
        # Ensure Volume is integer
        data['Volume'] = data['Volume'].astype(int)
        
        # Remove any rows with all NaN values
        data = data.dropna(how='all')
        
        # Sort by date (most recent first for display purposes)
        data = data.sort_index(ascending=True)
        
        return data
    
    def _get_period_days(self, period):
        """Convert period string to approximate number of days for filtering."""
        period_map = {
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825
        }
        return period_map.get(period, 180)
    
    def get_stock_info(self, symbol):
        """
        Get additional stock information like company name, sector, etc.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant information
            stock_info = {
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'beta': info.get('beta', 'N/A'),
                'currency': info.get('currency', 'INR')
            }
            
            return stock_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def validate_symbol(self, symbol):
        """
        Validate if a stock symbol exists and has data.
        
        Args:
            symbol (str): Stock symbol to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            data, found_symbol = self._try_symbol_variations(symbol, "5d")
            return data is not None and not data.empty
        except Exception:
            return False
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_market_movers(_self):
        """
        Get market movers for Indian stocks (simplified version).
        Note: This is a basic implementation. A full version would use market indices.
        
        Returns:
            dict: Market movers data
        """
        popular_stocks = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", 
            "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS"
        ]
        
        movers = {
            'gainers': [],
            'losers': [],
            'most_active': []
        }
        
        try:
            for symbol in popular_stocks:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="2d")
                
                if len(data) >= 2:
                    current = data['Close'].iloc[-1]
                    previous = data['Close'].iloc[-2]
                    change_pct = ((current - previous) / previous) * 100
                    volume = data['Volume'].iloc[-1]
                    
                    stock_data = {
                        'symbol': symbol,
                        'price': current,
                        'change_pct': change_pct,
                        'volume': volume
                    }
                    
                    if change_pct > 2:
                        movers['gainers'].append(stock_data)
                    elif change_pct < -2:
                        movers['losers'].append(stock_data)
                    
                    movers['most_active'].append(stock_data)
            
            # Sort lists
            movers['gainers'].sort(key=lambda x: x['change_pct'], reverse=True)
            movers['losers'].sort(key=lambda x: x['change_pct'])
            movers['most_active'].sort(key=lambda x: x['volume'], reverse=True)
            
            return movers
            
        except Exception as e:
            return {'error': str(e)}
