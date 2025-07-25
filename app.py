import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
from utils.stock_data import StockDataFetcher
from utils.chart_utils import create_price_chart, create_volume_chart
from utils.stock_database import search_stocks, get_popular_stocks, get_all_sectors, get_stocks_by_sector
from utils.watchlist_pages import render_watchlist_navigation
import io

# Page configuration
st.set_page_config(
    page_title="StockScope - Indian Market Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #00D4AA 0%, #00A3FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #8B949E;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .stock-card {
        background: linear-gradient(135deg, #1E1E2E 0%, #262738 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #00D4AA20;
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.1);
    }
    
    .metric-card {
        background: rgba(0, 212, 170, 0.1);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(0, 212, 170, 0.2);
    }
    
    .search-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(0, 212, 170, 0.2);
    }
    
    .suggestion-item {
        background: rgba(0, 212, 170, 0.1);
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        border: 1px solid rgba(0, 212, 170, 0.2);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .suggestion-item:hover {
        background: rgba(0, 212, 170, 0.2);
        border-color: #00D4AA;
    }
    
    .sector-tag {
        background: linear-gradient(90deg, #00D4AA, #00A3FF);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .popular-stock-btn {
        background: linear-gradient(135deg, #00D4AA 0%, #00A3FF 100%);
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
        color: white;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s ease;
        border: none;
        width: 100%;
    }
    
    .popular-stock-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 212, 170, 0.3);
    }
    
    .feature-highlight {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.1) 0%, rgba(0, 163, 255, 0.1) 100%);
        border-left: 4px solid #00D4AA;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = ""
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'show_suggestions' not in st.session_state:
    st.session_state.show_suggestions = False
if 'page_mode' not in st.session_state:
    st.session_state.page_mode = 'main'
# Initialize data fetcher
@st.cache_resource
def get_data_fetcher():
    return StockDataFetcher()

data_fetcher = get_data_fetcher()

if 'stock_fetcher' not in st.session_state:
    st.session_state.stock_fetcher = data_fetcher

# Check if we should render watchlist pages
if st.session_state.get('page_mode') == 'watchlist':
    # Add back to main button in sidebar
    with st.sidebar:
        if st.button("← Back to Main Analysis", use_container_width=True):
            st.session_state.page_mode = 'main'
            if 'selected_watchlist' in st.session_state:
                del st.session_state.selected_watchlist
            st.rerun()
    
    # Render watchlist pages
    render_watchlist_navigation()
    st.stop()

# Modern header for main app
st.markdown('<h1 class="main-header">📊 StockScope</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Advanced Indian Stock Market Analysis Platform</p>', unsafe_allow_html=True)

# Enhanced Sidebar with Modern Design
with st.sidebar:
    st.markdown("### 🔍 Smart Stock Search")
    
    # Smart search with autocomplete
    search_query = st.text_input(
        "Search stocks...",
        value=st.session_state.search_query,
        placeholder="Type symbol or company name (e.g., RELIANCE, TCS, Infosys)",
        help="Start typing to see suggestions",
        key="search_input"
    )
    
    # Initialize variables
    selected_stock = None
    full_symbol = None
    
    # Show suggestions when user types
    if search_query and len(search_query) >= 1:
        suggestions = search_stocks(search_query, limit=8)
        
        if suggestions:
            st.markdown("**📋 Suggestions:**")
            
            for i, stock in enumerate(suggestions):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if st.button(
                        f"**{stock['symbol']}** - {stock['name'][:30]}{'...' if len(stock['name']) > 30 else ''}",
                        key=f"suggestion_{i}",
                        help=f"{stock['name']} | {stock['sector']} | {stock['exchange']}"
                    ):
                        selected_stock = stock
                        full_symbol = stock['full_symbol']
                        st.session_state.search_query = stock['symbol']
                        st.rerun()
                
                with col2:
                    st.markdown(f'<span class="sector-tag">{stock["sector"]}</span>', unsafe_allow_html=True)
        else:
            st.info("🔍 No matches found. Try a different search term.")
    
    # Sector-based browsing
    st.markdown("---")
    st.markdown("### 🏢 Browse by Sector")
    
    sectors = get_all_sectors()
    selected_sector = st.selectbox(
        "Choose sector:",
        ["All Sectors"] + sectors,
        help="Filter stocks by business sector"
    )
    
    if selected_sector != "All Sectors":
        sector_stocks = get_stocks_by_sector(selected_sector)
        
        if sector_stocks:
            st.markdown(f"**{selected_sector} Stocks:**")
            
            for stock in sector_stocks[:6]:  # Show first 6
                if st.button(
                    f"{stock['symbol']} - {stock['name'][:25]}{'...' if len(stock['name']) > 25 else ''}",
                    key=f"sector_{stock['symbol']}",
                    help=f"{stock['name']} | {stock['exchange']}"
                ):
                    selected_stock = stock
                    full_symbol = stock['full_symbol']
                    st.session_state.search_query = stock['symbol']
                    st.rerun()
    
    # Time period selection with modern styling
    st.markdown("---")
    st.markdown("### ⏱️ Analysis Period")
    
    period_options = {
        "1 Month": "1mo",
        "3 Months": "3mo", 
        "6 Months": "6mo",
        "1 Year": "1y",
        "2 Years": "2y",
        "5 Years": "5y"
    }
    
    selected_period = st.selectbox(
        "Select time range:",
        list(period_options.keys()),
        index=3,  # Default to 1 year
        help="Choose the historical data period for analysis"
    )
    
    period = period_options[selected_period]
    
    # Enhanced analyze button
    st.markdown("---")
    
    # Use the selected stock or try to parse the search query
    if not selected_stock and search_query:
        # Try to find exact match
        exact_matches = search_stocks(search_query, limit=1)
        if exact_matches and exact_matches[0]['symbol'].lower() == search_query.lower():
            selected_stock = exact_matches[0]
            full_symbol = exact_matches[0]['full_symbol']
    
    analyze_disabled = not (selected_stock or full_symbol or search_query)
    
    if st.button(
        "🚀 Analyze Stock", 
        type="primary", 
        disabled=analyze_disabled,
        use_container_width=True,
        help="Click to fetch and analyze stock data"
    ):
        # Determine what to analyze
        symbol_to_analyze = full_symbol
        
        if not symbol_to_analyze and search_query:
            # Try to construct symbol from search query
            clean_query = search_query.upper().strip()
            if not clean_query.endswith(('.NS', '.BO')):
                symbol_to_analyze = f"{clean_query}.NS"  # Default to NSE
            else:
                symbol_to_analyze = clean_query
        
        if symbol_to_analyze:
            with st.spinner("🔄 Fetching market data..."):
                try:
                    stock_data = data_fetcher.fetch_stock_data(symbol_to_analyze, period)
                    if stock_data is not None:
                        st.session_state.stock_data = stock_data
                        st.session_state.selected_symbol = symbol_to_analyze
                        st.success(f"✅ Analysis ready for {symbol_to_analyze}")
                        st.balloons()  # Celebratory animation
                    else:
                        st.error("❌ Unable to fetch data. Please verify the stock symbol.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.error("❌ Please select a stock or enter a valid symbol.")
    
    # Quick access to popular stocks
    # Add Excel Watchlist navigation
    st.markdown("---")
    st.markdown("### 📊 Excel Watchlists")
    
    if st.button("📋 View Excel Watchlists", use_container_width=True, help="Analyze uploaded Excel file data"):
        st.session_state.page_mode = 'watchlist'
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ⭐ Popular Stocks")
    
    popular_list = get_popular_stocks(6)
    
    # Display popular stocks in a grid
    for i in range(0, len(popular_list), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            if i < len(popular_list):
                stock = popular_list[i]
                if st.button(
                    f"**{stock['symbol']}**",
                    key=f"popular_{i}",
                    help=f"{stock['name']} | {stock['sector']}",
                    use_container_width=True
                ):
                    st.session_state.search_query = stock['symbol']
                    selected_stock = stock
                    full_symbol = stock['full_symbol']
                    
                    with st.spinner(f"Loading {stock['symbol']}..."):
                        try:
                            stock_data = data_fetcher.fetch_stock_data(full_symbol, period)
                            if stock_data is not None:
                                st.session_state.stock_data = stock_data
                                st.session_state.selected_symbol = full_symbol
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        with col2:
            if i + 1 < len(popular_list):
                stock = popular_list[i + 1]
                if st.button(
                    f"**{stock['symbol']}**",
                    key=f"popular_{i+1}",
                    help=f"{stock['name']} | {stock['sector']}",
                    use_container_width=True
                ):
                    st.session_state.search_query = stock['symbol']
                    selected_stock = stock
                    full_symbol = stock['full_symbol']
                    
                    with st.spinner(f"Loading {stock['symbol']}..."):
                        try:
                            stock_data = data_fetcher.fetch_stock_data(full_symbol, period)
                            if stock_data is not None:
                                st.session_state.stock_data = stock_data
                                st.session_state.selected_symbol = full_symbol
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    
    # App info
    st.markdown("---")
    st.markdown("""
    <div class="feature-highlight">
        <strong>🎯 Features:</strong><br>
        • Smart autocomplete search<br>
        • Real-time market data<br>
        • Interactive charts<br>
        • Sector-wise browsing<br>
        • CSV data export
    </div>
    """, unsafe_allow_html=True)

# Enhanced Main Content Area
if st.session_state.stock_data is not None:
    stock_data = st.session_state.stock_data
    symbol = st.session_state.selected_symbol
    
    # Get stock info from database for better display
    symbol_clean = symbol.replace('.NS', '').replace('.BO', '')
    stock_info = None
    
    # Try to get additional info from our database
    from utils.stock_database import INDIAN_STOCKS
    if symbol_clean in INDIAN_STOCKS:
        stock_info = INDIAN_STOCKS[symbol_clean]
    
    # Modern stock header with company info
    st.markdown(f"""
    <div class="stock-card">
        <h2 style="margin-bottom: 0.5rem; color: #00D4AA;">
            {symbol} {f"- {stock_info['name']}" if stock_info else ""}
        </h2>
        {f'<p style="color: #8B949E; margin-bottom: 1rem;"><strong>Sector:</strong> {stock_info["sector"]} | <strong>Exchange:</strong> {stock_info["exchange"]}</p>' if stock_info else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced metrics with modern cards
    current_price = stock_data['Close'].iloc[-1]
    prev_price = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
    
    # Calculate additional metrics
    high_52w = stock_data['High'].max()
    low_52w = stock_data['Low'].min()
    avg_volume = stock_data['Volume'].mean()
    volume_change = ((stock_data['Volume'].iloc[-1] / stock_data['Volume'].iloc[-2] - 1) * 100) if len(stock_data) > 1 else 0
    
    # Price performance metrics
    period_return = ((current_price / stock_data['Close'].iloc[0]) - 1) * 100
    volatility = stock_data['Close'].pct_change().std() * 100
    
    # Display metrics in enhanced grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_color = "normal" if price_change >= 0 else "inverse"
        st.metric(
            label="💰 Current Price",
            value=f"₹{current_price:.2f}",
            delta=f"{price_change:.2f} ({price_change_pct:.2f}%)",
            delta_color=delta_color
        )
    
    with col2:
        volume_delta_color = "normal" if volume_change >= 0 else "inverse"
        st.metric(
            label="📊 Volume",
            value=f"{stock_data['Volume'].iloc[-1]:,.0f}",
            delta=f"{volume_change:.1f}%" if len(stock_data) > 1 else None,
            delta_color=volume_delta_color
        )
    
    with col3:
        st.metric(
            label="📈 52W High",
            value=f"₹{high_52w:.2f}",
            help=f"Distance from high: {((current_price/high_52w - 1) * 100):.1f}%"
        )
    
    with col4:
        st.metric(
            label="📉 52W Low",
            value=f"₹{low_52w:.2f}",
            help=f"Distance from low: {((current_price/low_52w - 1) * 100):.1f}%"
        )
    
    # Additional metrics row
    st.markdown("### 📊 Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        period_color = "normal" if period_return >= 0 else "inverse"
        st.metric(
            label=f"🎯 Period Return",
            value=f"{period_return:.2f}%",
            delta_color=period_color,
            help=f"Total return for the selected time period"
        )
    
    with col2:
        st.metric(
            label="📋 Avg Volume",
            value=f"{avg_volume:,.0f}",
            help="Average daily trading volume"
        )
    
    with col3:
        st.metric(
            label="⚡ Volatility",
            value=f"{volatility:.2f}%",
            help="Daily price volatility (standard deviation)"
        )
    
    with col4:
        market_cap_display = "N/A"
        if stock_info and 'market_cap' in stock_info:
            market_cap_display = stock_info.get('market_cap', 'N/A')
        
        st.metric(
            label="🏢 Market Cap",
            value=market_cap_display,
            help="Market capitalization"
        )
    
    st.markdown("---")
    
    # Enhanced Charts section with modern tabs
    st.markdown("### 📈 Interactive Charts")
    
    # Create tabs with icons
    chart_tab1, chart_tab2, chart_tab3 = st.tabs([
        "🕯️ Candlestick Chart", 
        "📊 Volume Analysis", 
        "📈 Price Trend"
    ])
    
    with chart_tab1:
        st.markdown("**Candlestick chart with moving averages and volume**")
        price_chart = create_price_chart(stock_data, symbol, chart_type="candlestick")
        st.plotly_chart(price_chart, use_container_width=True)
    
    with chart_tab2:
        st.markdown("**Volume analysis with moving average**")
        volume_chart = create_volume_chart(stock_data, symbol)
        st.plotly_chart(volume_chart, use_container_width=True)
    
    with chart_tab3:
        st.markdown("**Simple price trend line**")
        line_chart = create_price_chart(stock_data, symbol, chart_type="line")
        st.plotly_chart(line_chart, use_container_width=True)
    
    st.markdown("---")
    
    # Enhanced Data table section
    st.markdown("### 📊 Historical Data Explorer")
    
    # Modern display options with better layout
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        show_rows = st.selectbox(
            "📋 Rows to show:", 
            [10, 25, 50, 100, "All"],
            index=1,
            help="Number of rows to display in the table"
        )
    
    with col2:
        sort_column = st.selectbox(
            "🔤 Sort by:",
            ["Date", "Close", "Volume", "High", "Low", "Open"],
            index=0,
            help="Choose column to sort by"
        )
    
    with col3:
        sort_order = st.selectbox(
            "📈 Order:",
            ["Descending", "Ascending"],
            index=0,
            help="Sort order"
        )
    
    with col4:
        # Add period filter
        st.markdown("**📥 Download Data**")
        
        # Prepare CSV data
        csv_data = stock_data.copy()
        csv_data = csv_data.reset_index()
        
        # Create CSV buffer
        csv_buffer = io.StringIO()
        csv_data.to_csv(csv_buffer, index=False)
        csv_string = csv_buffer.getvalue()
        
        # Modern download button
        st.download_button(
            label="💾 Download CSV",
            data=csv_string,
            file_name=f"{symbol}_{selected_period.replace(' ', '_')}_data.csv",
            mime="text/csv",
            help="Download complete historical data",
            use_container_width=True
        )
    
    # Prepare and display enhanced data table
    display_data = stock_data.copy()
    display_data = display_data.reset_index()
    display_data['Date'] = display_data['Date'].dt.strftime('%Y-%m-%d')
    
    # Add daily change columns
    display_data['Daily Change (₹)'] = display_data['Close'] - display_data['Open']
    display_data['Daily Change (%)'] = ((display_data['Close'] - display_data['Open']) / display_data['Open'] * 100).round(2)
    
    # Round numeric columns
    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Adj Close']
    for col in numeric_columns:
        if col in display_data.columns:
            display_data[col] = display_data[col].round(2)
    
    # Sort data
    if sort_column == "Date":
        display_data = display_data.sort_values('Date', ascending=(sort_order == "Ascending"))
    else:
        display_data = display_data.sort_values(sort_column, ascending=(sort_order == "Ascending"))
    
    # Limit rows
    if show_rows != "All":
        display_data = display_data.head(show_rows)
    
    # Reorder columns for better presentation
    column_order = ['Date', 'Open', 'High', 'Low', 'Close', 'Daily Change (₹)', 'Daily Change (%)', 'Volume']
    if 'Adj Close' in display_data.columns:
        column_order.insert(-2, 'Adj Close')
    
    display_data = display_data[column_order]
    
    # Display enhanced table with styling
    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn("📅 Date"),
            "Open": st.column_config.NumberColumn("🔓 Open", format="₹%.2f"),
            "High": st.column_config.NumberColumn("📈 High", format="₹%.2f"),
            "Low": st.column_config.NumberColumn("📉 Low", format="₹%.2f"),
            "Close": st.column_config.NumberColumn("🔒 Close", format="₹%.2f"),
            "Daily Change (₹)": st.column_config.NumberColumn("💰 Change (₹)", format="₹%.2f"),
            "Daily Change (%)": st.column_config.NumberColumn("📊 Change (%)", format="%.2f%%"),
            "Volume": st.column_config.NumberColumn("📊 Volume", format="%d"),
            "Adj Close": st.column_config.NumberColumn("⚖️ Adj Close", format="₹%.2f") if 'Adj Close' in display_data.columns else None
        }
    )

else:
    # Modern Welcome Screen
    st.markdown("""
    <div class="feature-highlight">
        <h2 style="margin-bottom: 1rem; color: #00D4AA;">🎯 Welcome to StockScope!</h2>
        <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
            Your advanced platform for Indian stock market analysis with real-time data and intelligent insights.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature showcase
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stock-card">
            <h3 style="color: #00D4AA;">🔍 Smart Search</h3>
            <p>Type any stock symbol or company name to get intelligent suggestions with sector information.</p>
            <ul style="margin-top: 1rem;">
                <li>Auto-complete functionality</li>
                <li>Symbol & name search</li>
                <li>Sector-based browsing</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stock-card">
            <h3 style="color: #00A3FF;">📈 Advanced Charts</h3>
            <p>Interactive charts with multiple visualization options and technical indicators.</p>
            <ul style="margin-top: 1rem;">
                <li>Candlestick patterns</li>
                <li>Volume analysis</li>
                <li>Moving averages</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stock-card">
            <h3 style="color: #FF6B6B;">📊 Rich Analytics</h3>
            <p>Comprehensive data analysis with key performance metrics and downloadable reports.</p>
            <ul style="margin-top: 1rem;">
                <li>Performance metrics</li>
                <li>Historical data</li>
                <li>CSV export</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick start guide
    st.markdown("### 🚀 Quick Start Guide")
    
    step_col1, step_col2, step_col3, step_col4 = st.columns(4)
    
    with step_col1:
        st.markdown("""
        **Step 1️⃣**  
        🔍 **Search Stock**  
        Type symbol or company name in the sidebar
        """)
    
    with step_col2:
        st.markdown("""
        **Step 2️⃣**  
        ⏱️ **Select Period**  
        Choose your analysis timeframe
        """)
    
    with step_col3:
        st.markdown("""
        **Step 3️⃣**  
        🚀 **Analyze**  
        Click the analyze button to fetch data
        """)
    
    with step_col4:
        st.markdown("""
        **Step 4️⃣**  
        📊 **Explore**  
        View charts, metrics, and download data
        """)
    
    st.markdown("---")
    
    # Trending stocks showcase
    st.markdown("### ⭐ Popular Stocks to Explore")
    
    # Get popular stocks from database
    popular_list = get_popular_stocks(12)
    
    # Display in a modern grid layout
    for i in range(0, len(popular_list), 4):
        cols = st.columns(4)
        
        for j, col in enumerate(cols):
            if i + j < len(popular_list):
                stock = popular_list[i + j]
                
                with col:
                    if st.button(
                        f"**{stock['symbol']}**",
                        key=f"welcome_popular_{i+j}",
                        help=f"{stock['name']} | {stock['sector']}",
                        use_container_width=True
                    ):
                        st.session_state.search_query = stock['symbol']
                        
                        with st.spinner(f"Loading {stock['symbol']} data..."):
                            try:
                                stock_data = data_fetcher.fetch_stock_data(stock['full_symbol'], "1y")
                                if stock_data is not None:
                                    st.session_state.stock_data = stock_data
                                    st.session_state.selected_symbol = stock['full_symbol']
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error loading {stock['symbol']}: {str(e)}")
                    
                    # Show company info
                    st.caption(f"{stock['name'][:25]}{'...' if len(stock['name']) > 25 else ''}")
                    st.markdown(f'<span class="sector-tag">{stock["sector"]}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Market info section
    st.markdown("### 🏢 Supported Exchanges")
    
    exchange_col1, exchange_col2 = st.columns(2)
    
    with exchange_col1:
        st.markdown("""
        <div class="feature-highlight">
            <h4 style="color: #00D4AA;">NSE (National Stock Exchange)</h4>
            <p>India's leading stock exchange with largest market capitalization and trading volume.</p>
            <p><strong>Symbol Format:</strong> SYMBOL.NS</p>
        </div>
        """, unsafe_allow_html=True)
    
    with exchange_col2:
        st.markdown("""
        <div class="feature-highlight">
            <h4 style="color: #00A3FF;">BSE (Bombay Stock Exchange)</h4>
            <p>Asia's oldest stock exchange established in 1875, featuring over 5,000 listed companies.</p>
            <p><strong>Symbol Format:</strong> SYMBOL.BO</p>
        </div>
        """, unsafe_allow_html=True)

# Modern Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #8B949E; padding: 2rem; margin-top: 3rem;'>
    <div style='background: linear-gradient(135deg, rgba(0, 212, 170, 0.1) 0%, rgba(0, 163, 255, 0.1) 100%); 
                border-radius: 15px; padding: 1.5rem; margin-bottom: 1rem;'>
        <h4 style='color: #00D4AA; margin-bottom: 0.5rem;'>📊 StockScope - Advanced Market Analysis</h4>
        <p style='margin-bottom: 0.5rem;'>Powered by Yahoo Finance API | Built with Streamlit & Plotly</p>
        <p style='font-size: 0.9rem; color: #666;'>
            <strong>Features:</strong> Smart Search • Interactive Charts • Real-time Data • Sector Analysis
        </p>
    </div>
    <p style='font-size: 0.85rem; color: #8B949E;'>
        ⚠️ <strong>Disclaimer:</strong> This application is for educational and informational purposes only. 
        Not intended as investment advice. Please consult financial professionals before making investment decisions.
    </p>
    <p style='font-size: 0.8rem; color: #666; margin-top: 1rem;'>
        © 2024 StockScope | NSE & BSE Market Data
    </p>
</div>
""", unsafe_allow_html=True)
