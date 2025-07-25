import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
from utils.stock_data import StockDataFetcher
from utils.chart_utils import create_price_chart, create_volume_chart
import io

# Page configuration
st.set_page_config(
    page_title="Indian Stock Market Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = ""

# Initialize data fetcher
@st.cache_resource
def get_data_fetcher():
    return StockDataFetcher()

data_fetcher = get_data_fetcher()

# Main title and description
st.title("🇮🇳 Indian Stock Market Analysis")
st.markdown("---")

# Sidebar for stock selection and filters
with st.sidebar:
    st.header("Stock Selection")
    
    # Initialize variables
    symbol_input = ""
    exchange = "NSE (Default)"
    company_name = ""
    full_symbol = None
    
    # Popular stocks mapping for demo
    popular_stocks = {
        "Reliance Industries": "RELIANCE.NS",
        "Tata Consultancy Services": "TCS.NS",
        "HDFC Bank": "HDFCBANK.NS",
        "Infosys": "INFY.NS",
        "ICICI Bank": "ICICIBANK.NS",
        "State Bank of India": "SBIN.NS",
        "Bharti Airtel": "BHARTIARTL.NS",
        "ITC": "ITC.NS",
        "Kotak Mahindra Bank": "KOTAKBANK.NS",
        "Hindustan Unilever": "HINDUNILVR.NS"
    }
    
    # Stock input methods
    input_method = st.radio(
        "Choose input method:",
        ["Search by Symbol", "Search by Company Name"]
    )
    
    if input_method == "Search by Symbol":
        # Stock symbol input
        symbol_input = st.text_input(
            "Enter Stock Symbol:",
            placeholder="e.g., RELIANCE, TCS, HDFCBANK",
            help="Enter symbol without exchange suffix. The app will automatically try NSE first, then BSE."
        ).upper().strip()
        
        # Exchange selection
        exchange = st.selectbox(
            "Preferred Exchange:",
            ["NSE (Default)", "BSE", "Both (NSE first)"],
            help="NSE symbols end with .NS, BSE symbols end with .BO"
        )
        
        if symbol_input:
            if exchange == "NSE (Default)":
                full_symbol = f"{symbol_input}.NS"
            elif exchange == "BSE":
                full_symbol = f"{symbol_input}.BO"
            else:  # Both
                full_symbol = symbol_input  # Will be handled in fetch function
    else:
        # Company name search (simplified - in real app would have autocomplete)
        company_name = st.text_input(
            "Enter Company Name:",
            placeholder="e.g., Reliance Industries, Tata Consultancy Services"
        )
        
        if company_name:
            # Simple matching
            matches = [stock for stock in popular_stocks.keys() 
                      if company_name.lower() in stock.lower()]
            if matches:
                selected_company = st.selectbox("Select from matches:", matches)
                full_symbol = popular_stocks[selected_company]
            else:
                st.warning("Company not found in database. Try symbol search instead.")
                full_symbol = None
        else:
            full_symbol = None
    
    # Time period selection
    st.subheader("Analysis Period")
    period_options = {
        "1 Month": "1mo",
        "3 Months": "3mo", 
        "6 Months": "6mo",
        "1 Year": "1y",
        "2 Years": "2y",
        "5 Years": "5y"
    }
    
    selected_period = st.selectbox(
        "Select Time Period:",
        list(period_options.keys()),
        index=2  # Default to 6 months
    )
    
    period = period_options[selected_period]
    
    # Fetch data button
    if st.button("📊 Analyze Stock", type="primary"):
        if full_symbol:
            with st.spinner("Fetching stock data..."):
                try:
                    stock_data = data_fetcher.fetch_stock_data(full_symbol, period)
                    if stock_data is not None:
                        st.session_state.stock_data = stock_data
                        st.session_state.selected_symbol = full_symbol
                        st.success(f"✅ Data loaded for {full_symbol}")
                    else:
                        st.error("❌ Failed to fetch stock data. Please check the symbol and try again.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.error("❌ Please enter a stock symbol or company name.")

# Main content area
if st.session_state.stock_data is not None:
    stock_data = st.session_state.stock_data
    symbol = st.session_state.selected_symbol
    
    # Stock header information
    col1, col2, col3, col4 = st.columns(4)
    
    current_price = stock_data['Close'].iloc[-1]
    prev_price = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
    
    with col1:
        st.metric(
            label=f"**{symbol}**",
            value=f"₹{current_price:.2f}",
            delta=f"{price_change:.2f} ({price_change_pct:.2f}%)"
        )
    
    with col2:
        st.metric(
            label="Volume",
            value=f"{stock_data['Volume'].iloc[-1]:,.0f}",
            delta=f"{((stock_data['Volume'].iloc[-1] / stock_data['Volume'].iloc[-2] - 1) * 100):.1f}%" if len(stock_data) > 1 else None
        )
    
    with col3:
        high_52w = stock_data['High'].max()
        low_52w = stock_data['Low'].min()
        st.metric(
            label="52W High",
            value=f"₹{high_52w:.2f}"
        )
    
    with col4:
        st.metric(
            label="52W Low", 
            value=f"₹{low_52w:.2f}"
        )
    
    st.markdown("---")
    
    # Charts section
    st.subheader("📈 Price Charts")
    
    chart_tab1, chart_tab2 = st.tabs(["Price Chart", "Volume Chart"])
    
    with chart_tab1:
        price_chart = create_price_chart(stock_data, symbol)
        st.plotly_chart(price_chart, use_container_width=True)
    
    with chart_tab2:
        volume_chart = create_volume_chart(stock_data, symbol)
        st.plotly_chart(volume_chart, use_container_width=True)
    
    st.markdown("---")
    
    # Data table section
    st.subheader("📊 Historical Data")
    
    # Display options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_rows = st.selectbox(
            "Rows to display:", 
            [10, 25, 50, 100, "All"],
            index=1
        )
    
    with col2:
        sort_column = st.selectbox(
            "Sort by:",
            ["Date", "Close", "Volume", "High", "Low"],
            index=0
        )
    
    with col3:
        sort_order = st.selectbox(
            "Sort order:",
            ["Descending", "Ascending"],
            index=0
        )
    
    # Prepare data for display
    display_data = stock_data.copy()
    display_data = display_data.reset_index()
    display_data['Date'] = display_data['Date'].dt.strftime('%Y-%m-%d')
    
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
    
    # Display table
    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )
    
    # Download section
    st.subheader("💾 Download Data")
    
    # Prepare CSV data
    csv_data = stock_data.copy()
    csv_data = csv_data.reset_index()
    
    # Create CSV buffer
    csv_buffer = io.StringIO()
    csv_data.to_csv(csv_buffer, index=False)
    csv_string = csv_buffer.getvalue()
    
    # Download button
    st.download_button(
        label="📥 Download CSV",
        data=csv_string,
        file_name=f"{symbol}_{selected_period}_data.csv",
        mime="text/csv",
        help="Download historical stock data as CSV file"
    )
    
    # Additional metrics
    st.markdown("---")
    st.subheader("📊 Key Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_volume = stock_data['Volume'].mean()
        st.metric("Avg Volume", f"{avg_volume:,.0f}")
    
    with col2:
        volatility = stock_data['Close'].pct_change().std() * 100
        st.metric("Volatility", f"{volatility:.2f}%")
    
    with col3:
        returns = ((current_price / stock_data['Close'].iloc[0]) - 1) * 100
        st.metric(f"{selected_period} Return", f"{returns:.2f}%")
    
    with col4:
        avg_price = stock_data['Close'].mean()
        st.metric("Avg Price", f"₹{avg_price:.2f}")

else:
    # Welcome screen
    st.markdown("""
    ## Welcome to Indian Stock Market Analysis! 🎯
    
    ### How to use this app:
    1. **Select Input Method**: Choose to search by stock symbol or company name
    2. **Enter Stock Details**: Input the stock symbol (e.g., RELIANCE, TCS) or company name
    3. **Choose Exchange**: Select NSE (default) or BSE exchange
    4. **Select Time Period**: Choose analysis period from 1 month to 5 years
    5. **Click Analyze**: Get comprehensive stock analysis with charts and data
    
    ### Features:
    - 📈 **Interactive Charts**: Price and volume charts with zoom and hover
    - 📊 **Data Tables**: Sortable historical data with customizable views
    - 💾 **CSV Export**: Download stock data for external analysis
    - 🎯 **Key Metrics**: Current price, volume, 52-week high/low, returns
    - 🌙 **Dark Theme**: Easy on the eyes for extended analysis
    
    ### Supported Exchanges:
    - **NSE (National Stock Exchange)**: Primary Indian stock exchange
    - **BSE (Bombay Stock Exchange)**: Oldest stock exchange in Asia
    
    **Get started by entering a stock symbol in the sidebar!** 👈
    """)
    
    # Popular stocks quick access
    st.subheader("🔥 Popular Indian Stocks")
    
    popular_stocks_info = {
        "RELIANCE.NS": "Reliance Industries - Oil & Gas",
        "TCS.NS": "Tata Consultancy Services - IT Services", 
        "HDFCBANK.NS": "HDFC Bank - Banking",
        "INFY.NS": "Infosys - IT Services",
        "ICICIBANK.NS": "ICICI Bank - Banking",
        "SBIN.NS": "State Bank of India - Banking"
    }
    
    cols = st.columns(3)
    for i, (symbol, description) in enumerate(popular_stocks_info.items()):
        with cols[i % 3]:
            if st.button(f"📊 {symbol.replace('.NS', '')}", key=f"popular_{i}"):
                st.session_state.selected_symbol = symbol
                with st.spinner(f"Loading {symbol}..."):
                    try:
                        stock_data = data_fetcher.fetch_stock_data(symbol, "6mo")
                        if stock_data is not None:
                            st.session_state.stock_data = stock_data
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error loading {symbol}: {str(e)}")
            st.caption(description)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>📊 Indian Stock Market Analysis App | Data provided by Yahoo Finance</p>
    <p><small>⚠️ This is for educational purposes only. Not financial advice.</small></p>
</div>
""", unsafe_allow_html=True)
