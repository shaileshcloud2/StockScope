"""
Live data fetcher for Indian stocks from Yahoo Finance and NSE
Maps Excel data with actual stock symbols and fetches real-time data
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import logging
import time

logger = logging.getLogger(__name__)

class LiveDataFetcher:
    """Fetches live data for Indian stocks and maps Excel data with real stock names"""
    
    def __init__(self):
        self.stock_mapping = self._create_stock_mapping()
        self.cache_duration = 300  # 5 minutes cache
        
    def _create_stock_mapping(self) -> Dict[str, Dict[str, str]]:
        """Create mapping of price ranges and characteristics to actual stock symbols"""
        # Common Indian stocks with their Yahoo Finance symbols and characteristics
        stock_db = {
            # Large Cap Stocks
            "RELIANCE.NS": {"name": "Reliance Industries Ltd", "sector": "Oil & Gas", "mcap": "LC", "price_range": (2000, 3000)},
            "TCS.NS": {"name": "Tata Consultancy Services Ltd", "sector": "IT", "mcap": "LC", "price_range": (3000, 4500)},
            "HDFCBANK.NS": {"name": "HDFC Bank Ltd", "sector": "Banking", "mcap": "LC", "price_range": (1400, 1800)},
            "ICICIBANK.NS": {"name": "ICICI Bank Ltd", "sector": "Banking", "mcap": "LC", "price_range": (1000, 1400)},
            "INFY.NS": {"name": "Infosys Ltd", "sector": "IT", "mcap": "LC", "price_range": (1400, 2000)},
            "HINDUNILVR.NS": {"name": "Hindustan Unilever Ltd", "sector": "FMCG", "mcap": "LC", "price_range": (2200, 2800)},
            "LT.NS": {"name": "Larsen & Toubro Ltd", "sector": "Construction", "mcap": "LC", "price_range": (3000, 4000)},
            "SBIN.NS": {"name": "State Bank of India", "sector": "Banking", "mcap": "LC", "price_range": (600, 900)},
            "BHARTIARTL.NS": {"name": "Bharti Airtel Ltd", "sector": "Telecom", "mcap": "LC", "price_range": (1000, 1400)},
            "KOTAKBANK.NS": {"name": "Kotak Mahindra Bank Ltd", "sector": "Banking", "mcap": "LC", "price_range": (1600, 2000)},
            "ASIANPAINT.NS": {"name": "Asian Paints Ltd", "sector": "Paints", "mcap": "LC", "price_range": (2800, 3600)},
            "ITC.NS": {"name": "ITC Ltd", "sector": "FMCG", "mcap": "LC", "price_range": (400, 500)},
            "AXISBANK.NS": {"name": "Axis Bank Ltd", "sector": "Banking", "mcap": "LC", "price_range": (1000, 1300)},
            "MARUTI.NS": {"name": "Maruti Suzuki India Ltd", "sector": "Auto", "mcap": "LC", "price_range": (9000, 12000)},
            "SUNPHARMA.NS": {"name": "Sun Pharmaceutical Industries Ltd", "sector": "Pharma", "mcap": "LC", "price_range": (1400, 1800)},
            "ULTRACEMCO.NS": {"name": "UltraTech Cement Ltd", "sector": "Cement", "mcap": "LC", "price_range": (9000, 12000)},
            "TITAN.NS": {"name": "Titan Company Ltd", "sector": "Jewellery", "mcap": "LC", "price_range": (3000, 4000)},
            "NESTLEIND.NS": {"name": "Nestle India Ltd", "sector": "FMCG", "mcap": "LC", "price_range": (20000, 25000)},
            "BAJFINANCE.NS": {"name": "Bajaj Finance Ltd", "sector": "NBFC", "mcap": "LC", "price_range": (6000, 8000)},
            "WIPRO.NS": {"name": "Wipro Ltd", "sector": "IT", "mcap": "LC", "price_range": (400, 600)},
            
            # Mid Cap Stocks
            "ADANIGREEN.NS": {"name": "Adani Green Energy Ltd", "sector": "Power", "mcap": "MC", "price_range": (1000, 2000)},
            "ADANIPORTS.NS": {"name": "Adani Ports and SEZ Ltd", "sector": "Infrastructure", "mcap": "LC", "price_range": (700, 1000)},
            "BAJAJFINSV.NS": {"name": "Bajaj Finserv Ltd", "sector": "Financial Services", "mcap": "LC", "price_range": (1500, 2000)},
            "BAJAJ-AUTO.NS": {"name": "Bajaj Auto Ltd", "sector": "Auto", "mcap": "MC", "price_range": (8000, 10000)},
            "CIPLA.NS": {"name": "Cipla Ltd", "sector": "Pharma", "mcap": "MC", "price_range": (1300, 1700)},
            "COALINDIA.NS": {"name": "Coal India Ltd", "sector": "Mining", "mcap": "LC", "price_range": (300, 500)},
            "DRREDDY.NS": {"name": "Dr Reddy's Laboratories Ltd", "sector": "Pharma", "mcap": "MC", "price_range": (5000, 7000)},
            "EICHERMOT.NS": {"name": "Eicher Motors Ltd", "sector": "Auto", "mcap": "MC", "price_range": (4000, 5000)},
            "GRASIM.NS": {"name": "Grasim Industries Ltd", "sector": "Chemicals", "mcap": "MC", "price_range": (2000, 2500)},
            "HCLTECH.NS": {"name": "HCL Technologies Ltd", "sector": "IT", "mcap": "LC", "price_range": (1200, 1600)},
            "HEROMOTOCO.NS": {"name": "Hero MotoCorp Ltd", "sector": "Auto", "mcap": "MC", "price_range": (4000, 5000)},
            "HINDALCO.NS": {"name": "Hindalco Industries Ltd", "sector": "Metals", "mcap": "MC", "price_range": (400, 600)},
            "INDUSINDBK.NS": {"name": "IndusInd Bank Ltd", "sector": "Banking", "mcap": "MC", "price_range": (1000, 1400)},
            "JSWSTEEL.NS": {"name": "JSW Steel Ltd", "sector": "Steel", "mcap": "MC", "price_range": (800, 1000)},
            "ONGC.NS": {"name": "Oil & Natural Gas Corp Ltd", "sector": "Oil & Gas", "mcap": "LC", "price_range": (200, 300)},
            "POWERGRID.NS": {"name": "Power Grid Corp of India Ltd", "sector": "Power", "mcap": "LC", "price_range": (200, 300)},
            "TATAMOTORS.NS": {"name": "Tata Motors Ltd", "sector": "Auto", "mcap": "MC", "price_range": (700, 1000)},
            "TATASTEEL.NS": {"name": "Tata Steel Ltd", "sector": "Steel", "mcap": "MC", "price_range": (100, 200)},
            "TECHM.NS": {"name": "Tech Mahindra Ltd", "sector": "IT", "mcap": "MC", "price_range": (1400, 1800)},
            "VEDL.NS": {"name": "Vedanta Ltd", "sector": "Metals", "mcap": "MC", "price_range": (400, 600)},
            
            # Small Cap and Specialized Stocks
            "ADANIENT.NS": {"name": "Adani Enterprises Ltd", "sector": "Infrastructure", "mcap": "LC", "price_range": (2000, 3000)},
            "APOLLOHOSP.NS": {"name": "Apollo Hospitals Enterprise Ltd", "sector": "Healthcare", "mcap": "MC", "price_range": (5000, 7000)},
            "BPCL.NS": {"name": "Bharat Petroleum Corp Ltd", "sector": "Oil & Gas", "mcap": "MC", "price_range": (300, 400)},
            "BRITANNIA.NS": {"name": "Britannia Industries Ltd", "sector": "FMCG", "mcap": "MC", "price_range": (4500, 5500)},
            "DIVISLAB.NS": {"name": "Divi's Laboratories Ltd", "sector": "Pharma", "mcap": "MC", "price_range": (3500, 4500)},
            "GODREJCP.NS": {"name": "Godrej Consumer Products Ltd", "sector": "FMCG", "mcap": "MC", "price_range": (1000, 1300)},
            "HDFCLIFE.NS": {"name": "HDFC Life Insurance Company Ltd", "sector": "Insurance", "mcap": "MC", "price_range": (600, 800)},
            "IOC.NS": {"name": "Indian Oil Corp Ltd", "sector": "Oil & Gas", "mcap": "MC", "price_range": (100, 200)},
            "LTIM.NS": {"name": "LTIMindtree Ltd", "sector": "IT", "mcap": "MC", "price_range": (5000, 6000)},
            "M&M.NS": {"name": "Mahindra & Mahindra Ltd", "sector": "Auto", "mcap": "MC", "price_range": (2500, 3000)},
            "PIDILITIND.NS": {"name": "Pidilite Industries Ltd", "sector": "Chemicals", "mcap": "MC", "price_range": (2500, 3000)},
            "SBILIFE.NS": {"name": "SBI Life Insurance Company Ltd", "sector": "Insurance", "mcap": "MC", "price_range": (1200, 1600)},
            "TATACONSUM.NS": {"name": "Tata Consumer Products Ltd", "sector": "FMCG", "mcap": "MC", "price_range": (900, 1200)},
            
            # Banking and Financial Services
            "BANDHANBNK.NS": {"name": "Bandhan Bank Ltd", "sector": "Banking", "mcap": "SC", "price_range": (200, 300)},
            "FEDERALBNK.NS": {"name": "Federal Bank Ltd", "sector": "Banking", "mcap": "SC", "price_range": (100, 200)},
            "IDFCFIRSTB.NS": {"name": "IDFC First Bank Ltd", "sector": "Banking", "mcap": "SC", "price_range": (60, 100)},
            "PNB.NS": {"name": "Punjab National Bank", "sector": "Banking", "mcap": "MC", "price_range": (80, 120)},
            "CANBK.NS": {"name": "Canara Bank", "sector": "Banking", "mcap": "MC", "price_range": (100, 150)},
            
            # IT and Technology
            "MPHASIS.NS": {"name": "Mphasis Ltd", "sector": "IT", "mcap": "SC", "price_range": (2500, 3000)},
            "PERSISTENT.NS": {"name": "Persistent Systems Ltd", "sector": "IT", "mcap": "SC", "price_range": (4000, 5000)},
            "COFORGE.NS": {"name": "Coforge Ltd", "sector": "IT", "mcap": "SC", "price_range": (6000, 8000)},
            
            # Pharma and Healthcare
            "BIOCON.NS": {"name": "Biocon Ltd", "sector": "Pharma", "mcap": "SC", "price_range": (300, 400)},
            "LUPIN.NS": {"name": "Lupin Ltd", "sector": "Pharma", "mcap": "SC", "price_range": (1000, 1500)},
            "TORNTPHARM.NS": {"name": "Torrent Pharmaceuticals Ltd", "sector": "Pharma", "mcap": "MC", "price_range": (2000, 3000)},
        }
        
        return stock_db
    
    def identify_stock_from_price(self, price: float, suggestion: Optional[str] = None, mcap: Optional[str] = None, sector: Optional[str] = None) -> Optional[str]:
        """Identify stock symbol based on price and other characteristics"""
        candidates = []
        
        for symbol, info in self.stock_mapping.items():
            price_min, price_max = info['price_range']
            
            # Check if price is within range (with some tolerance)
            tolerance = 0.2  # 20% tolerance
            adjusted_min = float(price_min) * (1 - tolerance)
            adjusted_max = float(price_max) * (1 + tolerance)
            
            if adjusted_min <= price <= adjusted_max:
                score = 100  # Base score for price match
                
                # Add bonus for mcap match
                if mcap and info['mcap'] == mcap:
                    score += 50
                
                # Add bonus for sector match
                if sector and isinstance(sector, str) and any(keyword in sector.lower() for keyword in info['sector'].lower().split()):
                    score += 30
                
                candidates.append((symbol, score, info))
        
        if candidates:
            # Return the best match
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        return None
    
    def fetch_live_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch live data for multiple symbols"""
        live_data = {}
        
        # Process symbols in batches to avoid rate limiting
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            try:
                # Fetch data for batch
                batch_str = " ".join(batch)
                data = yf.download(batch_str, period="1d", interval="1m", progress=False)
                
                if data is None or data.empty:
                    continue
                
                # Process each symbol in the batch
                for symbol in batch:
                    try:
                        if len(batch) == 1:
                            symbol_data = data
                        else:
                            symbol_data = data.xs(symbol, level=1, axis=1)
                        
                        if symbol_data is not None and not symbol_data.empty:
                            latest = symbol_data.iloc[-1]
                            previous = symbol_data.iloc[-2] if len(symbol_data) > 1 else latest
                            
                            live_data[symbol] = {
                                'current_price': latest['Close'],
                                'previous_close': previous['Close'],
                                'high': latest['High'],
                                'low': latest['Low'],
                                'volume': int(latest['Volume']),
                                'change': latest['Close'] - previous['Close'],
                                'change_percent': ((latest['Close'] - previous['Close']) / previous['Close']) * 100,
                                'last_updated': datetime.now().strftime('%H:%M:%S')
                            }
                    
                    except Exception as e:
                        logger.warning(f"Error processing {symbol}: {str(e)}")
                        continue
            
            except Exception as e:
                logger.error(f"Error fetching batch {batch}: {str(e)}")
                continue
            
            # Add delay between batches
            time.sleep(0.5)
        
        return live_data
    
    def enhance_excel_data(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """Enhance Excel data with live stock information and actual names"""
        enhanced_df = df.copy()
        
        # Find price column
        price_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['price', 'close'])]
        if not price_cols:
            return enhanced_df
        
        price_col = price_cols[0]
        
        # Initialize new columns
        enhanced_df['Identified_Symbol'] = None
        enhanced_df['Stock_Name'] = None
        enhanced_df['Live_Price'] = None
        enhanced_df['Live_Change'] = None
        enhanced_df['Live_Change_Percent'] = None
        enhanced_df['Last_Updated'] = None
        
        # Identify stocks and fetch live data
        symbols_to_fetch = []
        symbol_mapping = {}
        
        for idx, row in df.iterrows():
            if pd.isna(row[price_col]):
                continue
            
            price = float(row[price_col])
            suggestion = str(row.get('Suggestion', '')) if pd.notna(row.get('Suggestion')) else None
            mcap = str(row.get('M Cap', '')) if pd.notna(row.get('M Cap')) else None
            industry = str(row.get('Industry', '')) if pd.notna(row.get('Industry')) else None
            
            # Try to identify the stock
            identified_symbol = self.identify_stock_from_price(price, suggestion, mcap, industry)
            
            if identified_symbol:
                enhanced_df.at[idx, 'Identified_Symbol'] = identified_symbol
                enhanced_df.at[idx, 'Stock_Name'] = self.stock_mapping[identified_symbol]['name']
                symbols_to_fetch.append(identified_symbol)
                symbol_mapping[identified_symbol] = idx
        
        # Fetch live data for identified symbols
        if symbols_to_fetch:
            live_data = self.fetch_live_data(list(set(symbols_to_fetch)))
            
            # Update dataframe with live data
            for symbol, data in live_data.items():
                if symbol in symbol_mapping:
                    idx = symbol_mapping[symbol]
                    enhanced_df.at[idx, 'Live_Price'] = round(data['current_price'], 2)
                    enhanced_df.at[idx, 'Live_Change'] = round(data['change'], 2)
                    enhanced_df.at[idx, 'Live_Change_Percent'] = round(data['change_percent'], 2)
                    enhanced_df.at[idx, 'Last_Updated'] = data['last_updated']
        
        return enhanced_df
    
    def get_stock_suggestions(self, price_range: Optional[Tuple[float, float]] = None, sector: Optional[str] = None, mcap: Optional[str] = None) -> List[Dict]:
        """Get stock suggestions based on criteria"""
        suggestions = []
        
        for symbol, info in self.stock_mapping.items():
            # Apply filters
            if price_range:
                stock_min, stock_max = info['price_range']
                if not (price_range[0] <= stock_max and price_range[1] >= stock_min):
                    continue
            
            if sector and isinstance(sector, str) and sector.lower() not in info['sector'].lower():
                continue
            
            if mcap and mcap != info['mcap']:
                continue
            
            suggestions.append({
                'symbol': symbol,
                'name': info['name'],
                'sector': info['sector'],
                'mcap': info['mcap'],
                'price_range': info['price_range']
            })
        
        return suggestions

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_live_data_fetcher():
    """Get cached live data fetcher instance"""
    return LiveDataFetcher()

def refresh_live_data(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """Refresh live data for the dataframe"""
    fetcher = get_live_data_fetcher()
    return fetcher.enhance_excel_data(df, sheet_name)