"""
Stock database for autocomplete functionality
Contains popular Indian stocks from NSE and BSE
"""

# Comprehensive list of popular Indian stocks
INDIAN_STOCKS = {
    # Banking & Financial Services
    "HDFCBANK": {"name": "HDFC Bank Limited", "symbol": "HDFCBANK.NS", "sector": "Banking", "exchange": "NSE"},
    "ICICIBANK": {"name": "ICICI Bank Limited", "symbol": "ICICIBANK.NS", "sector": "Banking", "exchange": "NSE"},
    "SBIN": {"name": "State Bank of India", "symbol": "SBIN.NS", "sector": "Banking", "exchange": "NSE"},
    "KOTAKBANK": {"name": "Kotak Mahindra Bank", "symbol": "KOTAKBANK.NS", "sector": "Banking", "exchange": "NSE"},
    "AXISBANK": {"name": "Axis Bank Limited", "symbol": "AXISBANK.NS", "sector": "Banking", "exchange": "NSE"},
    "INDUSIND": {"name": "IndusInd Bank Limited", "symbol": "INDUSINDBK.NS", "sector": "Banking", "exchange": "NSE"},
    "BANDHANBNK": {"name": "Bandhan Bank Limited", "symbol": "BANDHANBNK.NS", "sector": "Banking", "exchange": "NSE"},
    
    # IT Services
    "TCS": {"name": "Tata Consultancy Services", "symbol": "TCS.NS", "sector": "IT Services", "exchange": "NSE"},
    "INFY": {"name": "Infosys Limited", "symbol": "INFY.NS", "sector": "IT Services", "exchange": "NSE"},
    "WIPRO": {"name": "Wipro Limited", "symbol": "WIPRO.NS", "sector": "IT Services", "exchange": "NSE"},
    "HCLTECH": {"name": "HCL Technologies", "symbol": "HCLTECH.NS", "sector": "IT Services", "exchange": "NSE"},
    "TECHM": {"name": "Tech Mahindra Limited", "symbol": "TECHM.NS", "sector": "IT Services", "exchange": "NSE"},
    "LTI": {"name": "L&T Infotech Limited", "symbol": "LTI.NS", "sector": "IT Services", "exchange": "NSE"},
    
    # Oil & Gas
    "RELIANCE": {"name": "Reliance Industries", "symbol": "RELIANCE.NS", "sector": "Oil & Gas", "exchange": "NSE"},
    "ONGC": {"name": "Oil & Natural Gas Corp", "symbol": "ONGC.NS", "sector": "Oil & Gas", "exchange": "NSE"},
    "IOC": {"name": "Indian Oil Corporation", "symbol": "IOC.NS", "sector": "Oil & Gas", "exchange": "NSE"},
    "BPCL": {"name": "Bharat Petroleum Corp", "symbol": "BPCL.NS", "sector": "Oil & Gas", "exchange": "NSE"},
    "HPCL": {"name": "Hindustan Petroleum", "symbol": "HPCL.NS", "sector": "Oil & Gas", "exchange": "NSE"},
    
    # Automotive
    "MARUTI": {"name": "Maruti Suzuki India", "symbol": "MARUTI.NS", "sector": "Automotive", "exchange": "NSE"},
    "TATAMOTORS": {"name": "Tata Motors Limited", "symbol": "TATAMOTORS.NS", "sector": "Automotive", "exchange": "NSE"},
    "M&M": {"name": "Mahindra & Mahindra", "symbol": "M&M.NS", "sector": "Automotive", "exchange": "NSE"},
    "BAJAJ-AUTO": {"name": "Bajaj Auto Limited", "symbol": "BAJAJ-AUTO.NS", "sector": "Automotive", "exchange": "NSE"},
    "HEROMOTOCO": {"name": "Hero MotoCorp Limited", "symbol": "HEROMOTOCO.NS", "sector": "Automotive", "exchange": "NSE"},
    "EICHERMOT": {"name": "Eicher Motors Limited", "symbol": "EICHERMOT.NS", "sector": "Automotive", "exchange": "NSE"},
    
    # FMCG
    "HINDUNILVR": {"name": "Hindustan Unilever", "symbol": "HINDUNILVR.NS", "sector": "FMCG", "exchange": "NSE"},
    "ITC": {"name": "ITC Limited", "symbol": "ITC.NS", "sector": "FMCG", "exchange": "NSE"},
    "NESTLEIND": {"name": "Nestle India Limited", "symbol": "NESTLEIND.NS", "sector": "FMCG", "exchange": "NSE"},
    "BRITANNIA": {"name": "Britannia Industries", "symbol": "BRITANNIA.NS", "sector": "FMCG", "exchange": "NSE"},
    "DABUR": {"name": "Dabur India Limited", "symbol": "DABUR.NS", "sector": "FMCG", "exchange": "NSE"},
    "GODREJCP": {"name": "Godrej Consumer Products", "symbol": "GODREJCP.NS", "sector": "FMCG", "exchange": "NSE"},
    
    # Telecom
    "BHARTIARTL": {"name": "Bharti Airtel Limited", "symbol": "BHARTIARTL.NS", "sector": "Telecom", "exchange": "NSE"},
    "IDEA": {"name": "Vodafone Idea Limited", "symbol": "IDEA.NS", "sector": "Telecom", "exchange": "NSE"},
    
    # Pharmaceuticals
    "SUNPHARMA": {"name": "Sun Pharmaceutical", "symbol": "SUNPHARMA.NS", "sector": "Pharma", "exchange": "NSE"},
    "DRREDDY": {"name": "Dr. Reddy's Laboratories", "symbol": "DRREDDY.NS", "sector": "Pharma", "exchange": "NSE"},
    "CIPLA": {"name": "Cipla Limited", "symbol": "CIPLA.NS", "sector": "Pharma", "exchange": "NSE"},
    "DIVISLAB": {"name": "Divi's Laboratories", "symbol": "DIVISLAB.NS", "sector": "Pharma", "exchange": "NSE"},
    "BIOCON": {"name": "Biocon Limited", "symbol": "BIOCON.NS", "sector": "Pharma", "exchange": "NSE"},
    "LUPIN": {"name": "Lupin Limited", "symbol": "LUPIN.NS", "sector": "Pharma", "exchange": "NSE"},
    
    # Metals & Mining
    "TATASTEEL": {"name": "Tata Steel Limited", "symbol": "TATASTEEL.NS", "sector": "Metals", "exchange": "NSE"},
    "JSWSTEEL": {"name": "JSW Steel Limited", "symbol": "JSWSTEEL.NS", "sector": "Metals", "exchange": "NSE"},
    "HINDALCO": {"name": "Hindalco Industries", "symbol": "HINDALCO.NS", "sector": "Metals", "exchange": "NSE"},
    "VEDL": {"name": "Vedanta Limited", "symbol": "VEDL.NS", "sector": "Metals", "exchange": "NSE"},
    "COALINDIA": {"name": "Coal India Limited", "symbol": "COALINDIA.NS", "sector": "Mining", "exchange": "NSE"},
    "NATIONALUM": {"name": "National Aluminium", "symbol": "NATIONALUM.NS", "sector": "Metals", "exchange": "NSE"},
    
    # Cement
    "ULTRACEMCO": {"name": "UltraTech Cement", "symbol": "ULTRACEMCO.NS", "sector": "Cement", "exchange": "NSE"},
    "SHREECEM": {"name": "Shree Cement Limited", "symbol": "SHREECEM.NS", "sector": "Cement", "exchange": "NSE"},
    "GRASIM": {"name": "Grasim Industries", "symbol": "GRASIM.NS", "sector": "Cement", "exchange": "NSE"},
    "ACC": {"name": "ACC Limited", "symbol": "ACC.NS", "sector": "Cement", "exchange": "NSE"},
    "AMBUJACEM": {"name": "Ambuja Cements", "symbol": "AMBUJACEM.NS", "sector": "Cement", "exchange": "NSE"},
    
    # Power
    "POWERGRID": {"name": "Power Grid Corp of India", "symbol": "POWERGRID.NS", "sector": "Power", "exchange": "NSE"},
    "NTPC": {"name": "NTPC Limited", "symbol": "NTPC.NS", "sector": "Power", "exchange": "NSE"},
    "TATAPOWER": {"name": "Tata Power Company", "symbol": "TATAPOWER.NS", "sector": "Power", "exchange": "NSE"},
    "ADANIPOWER": {"name": "Adani Power Limited", "symbol": "ADANIPOWER.NS", "sector": "Power", "exchange": "NSE"},
    
    # Infrastructure
    "LT": {"name": "Larsen & Toubro", "symbol": "LT.NS", "sector": "Infrastructure", "exchange": "NSE"},
    "ADANIPORTS": {"name": "Adani Ports & SEZ", "symbol": "ADANIPORTS.NS", "sector": "Infrastructure", "exchange": "NSE"},
    
    # Airlines
    "INDIGO": {"name": "InterGlobe Aviation", "symbol": "INDIGO.NS", "sector": "Airlines", "exchange": "NSE"},
    "SPICEJET": {"name": "SpiceJet Limited", "symbol": "SPICEJET.NS", "sector": "Airlines", "exchange": "NSE"},
    
    # Retail
    "DMART": {"name": "Avenue Supermarts", "symbol": "DMART.NS", "sector": "Retail", "exchange": "NSE"},
    "TRENT": {"name": "Trent Limited", "symbol": "TRENT.NS", "sector": "Retail", "exchange": "NSE"},
    
    # Real Estate
    "DLF": {"name": "DLF Limited", "symbol": "DLF.NS", "sector": "Real Estate", "exchange": "NSE"},
    "GODREJPROP": {"name": "Godrej Properties", "symbol": "GODREJPROP.NS", "sector": "Real Estate", "exchange": "NSE"},
    
    # Insurance
    "SBILIFE": {"name": "SBI Life Insurance", "symbol": "SBILIFE.NS", "sector": "Insurance", "exchange": "NSE"},
    "ICICIPRULI": {"name": "ICICI Prudential Life", "symbol": "ICICIPRULI.NS", "sector": "Insurance", "exchange": "NSE"},
    "HDFCLIFE": {"name": "HDFC Life Insurance", "symbol": "HDFCLIFE.NS", "sector": "Insurance", "exchange": "NSE"},
}

def search_stocks(query, limit=10):
    """
    Search for stocks based on symbol or company name
    
    Args:
        query (str): Search query
        limit (int): Maximum number of results to return
    
    Returns:
        list: List of matching stocks
    """
    query = query.lower().strip()
    if not query:
        return []
    
    matches = []
    
    # Search by symbol first (exact and partial matches)
    for symbol, data in INDIAN_STOCKS.items():
        if symbol.lower().startswith(query):
            matches.append({
                "symbol": symbol,
                "full_symbol": data["symbol"],
                "name": data["name"],
                "sector": data["sector"],
                "exchange": data["exchange"],
                "match_type": "symbol_exact"
            })
    
    # Search by company name
    for symbol, data in INDIAN_STOCKS.items():
        name_lower = data["name"].lower()
        if query in name_lower and not any(m["symbol"] == symbol for m in matches):
            matches.append({
                "symbol": symbol,
                "full_symbol": data["symbol"],
                "name": data["name"],
                "sector": data["sector"],
                "exchange": data["exchange"],
                "match_type": "name"
            })
    
    # Search by partial symbol match (if not already found)
    for symbol, data in INDIAN_STOCKS.items():
        if query in symbol.lower() and not any(m["symbol"] == symbol for m in matches):
            matches.append({
                "symbol": symbol,
                "full_symbol": data["symbol"],
                "name": data["name"],
                "sector": data["sector"],
                "exchange": data["exchange"],
                "match_type": "symbol_partial"
            })
    
    # Sort matches by relevance
    def sort_key(match):
        if match["match_type"] == "symbol_exact":
            return 0
        elif match["match_type"] == "name" and match["name"].lower().startswith(query):
            return 1
        elif match["match_type"] == "name":
            return 2
        else:
            return 3
    
    matches.sort(key=sort_key)
    return matches[:limit]

def get_popular_stocks(limit=12):
    """
    Get popular stocks for quick access
    
    Args:
        limit (int): Number of popular stocks to return
    
    Returns:
        list: List of popular stocks
    """
    popular_symbols = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN",
        "BHARTIARTL", "ITC", "KOTAKBANK", "HINDUNILVR", "MARUTI", "SUNPHARMA"
    ]
    
    popular_stocks = []
    for symbol in popular_symbols[:limit]:
        if symbol in INDIAN_STOCKS:
            data = INDIAN_STOCKS[symbol]
            popular_stocks.append({
                "symbol": symbol,
                "full_symbol": data["symbol"],
                "name": data["name"],
                "sector": data["sector"],
                "exchange": data["exchange"]
            })
    
    return popular_stocks

def get_stocks_by_sector(sector):
    """
    Get stocks filtered by sector
    
    Args:
        sector (str): Sector name
    
    Returns:
        list: List of stocks in the sector
    """
    stocks = []
    for symbol, data in INDIAN_STOCKS.items():
        if data["sector"].lower() == sector.lower():
            stocks.append({
                "symbol": symbol,
                "full_symbol": data["symbol"],
                "name": data["name"],
                "sector": data["sector"],
                "exchange": data["exchange"]
            })
    
    return stocks

def get_all_sectors():
    """
    Get all available sectors
    
    Returns:
        list: List of unique sectors
    """
    sectors = set()
    for data in INDIAN_STOCKS.values():
        sectors.add(data["sector"])
    
    return sorted(list(sectors))