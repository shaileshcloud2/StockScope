import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
from utils.stock_data import StockDataFetcher
from utils.chart_utils import create_price_chart, create_volume_chart, detect_golden_death_cross, create_cross_analysis_chart
from utils.stock_database import search_stocks, get_popular_stocks, get_all_sectors, get_stocks_by_sector
from utils.watchlist_pages import render_watchlist_navigation
from utils.nse500_analyzer import analyze_nse500_crosses, filter_results, get_rsi_education, calculate_rsi, detect_divergence
from utils.market_analysis_report import generate_market_analysis_report, render_pattern_chart
from utils.ath_breakout_report import generate_ath_breakout_report, render_ath_chart
from screener_server import run_scan_direct as _run_scan_direct
import streamlit.components.v1 as _components
import io

# Page configuration
st.set_page_config(
    page_title="StockScope - Indian Market Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern colorful UI
st.markdown("""
<style>
    /* Main background with gradient */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 2px solid #00D4AA;
    }
    
    .main-header {
        background: linear-gradient(90deg, #00D4AA 0%, #7B68EE 50%, #FF6B6B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(0, 212, 170, 0.5);
    }
    
    .subtitle {
        text-align: center;
        background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.3rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    .stock-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid rgba(0, 212, 170, 0.4);
        box-shadow: 0 10px 40px rgba(0, 212, 170, 0.2), 0 0 20px rgba(123, 104, 238, 0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(123, 104, 238, 0.2) 0%, rgba(0, 212, 170, 0.2) 100%);
        border-radius: 15px;
        padding: 1.2rem;
        text-align: center;
        border: 1px solid rgba(123, 104, 238, 0.4);
        box-shadow: 0 4px 15px rgba(123, 104, 238, 0.2);
    }
    
    .search-container {
        background: linear-gradient(135deg, rgba(30, 60, 114, 0.5) 0%, rgba(42, 82, 152, 0.5) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(0, 212, 170, 0.3);
    }
    
    .suggestion-item {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.15) 0%, rgba(123, 104, 238, 0.15) 100%);
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        border: 1px solid rgba(0, 212, 170, 0.3);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .suggestion-item:hover {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.3) 0%, rgba(123, 104, 238, 0.3) 100%);
        border-color: #00D4AA;
        transform: translateX(5px);
    }
    
    .sector-tag {
        background: linear-gradient(90deg, #FF6B6B, #FFE66D, #4ECDC4);
        color: #1a1a2e;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .popular-stock-btn {
        background: linear-gradient(135deg, #00D4AA 0%, #7B68EE 100%);
        border-radius: 12px;
        padding: 0.8rem;
        text-align: center;
        color: white;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        border: none;
        width: 100%;
    }
    
    .popular-stock-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(123, 104, 238, 0.4);
    }
    
    .feature-highlight {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.15) 0%, rgba(123, 104, 238, 0.15) 50%, rgba(255, 107, 107, 0.15) 100%);
        border-left: 4px solid;
        border-image: linear-gradient(180deg, #00D4AA, #7B68EE, #FF6B6B) 1;
        padding: 1.2rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
    }
    
    /* Colorful metric styling */
    [data-testid="stMetricValue"] {
        color: #00D4AA !important;
        font-weight: 700;
    }
    
    [data-testid="stMetricDelta"] svg {
        stroke: #00D4AA;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #00D4AA 0%, #7B68EE 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(123, 104, 238, 0.4);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%);
        color: #1a1a2e;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(90deg, rgba(0, 212, 170, 0.1), rgba(123, 104, 238, 0.1));
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #a8edea;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00D4AA 0%, #7B68EE 100%);
        border-radius: 8px;
    }
    
    /* DataFrame styling */
    [data-testid="stDataFrame"] {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.15);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: linear-gradient(135deg, rgba(30, 60, 114, 0.8) 0%, rgba(42, 82, 152, 0.8) 100%);
        border: 1px solid rgba(0, 212, 170, 0.3);
        border-radius: 10px;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        background: linear-gradient(135deg, rgba(30, 60, 114, 0.8) 0%, rgba(42, 82, 152, 0.8) 100%);
        border: 1px solid rgba(0, 212, 170, 0.3);
        border-radius: 10px;
        color: white;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.1) 0%, rgba(123, 104, 238, 0.1) 100%);
        border-radius: 10px;
    }
    
    /* Golden/Death cross markers */
    .golden-marker {
        color: #00FF00;
        font-weight: bold;
    }
    
    .death-marker {
        color: #FF4444;
        font-weight: bold;
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

# Check if we should render lifetime high report
if st.session_state.get('page_mode') == 'lifetime_high_report':
    with st.sidebar:
        if st.button("← Back to Main Analysis", use_container_width=True):
            st.session_state.page_mode = 'main'
            st.rerun()
    
    st.markdown('<h1 class="main-header">🏆 Lifetime High Report</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Stocks within 2% of Lifetime High with Cup & Handle Pattern</p>', unsafe_allow_html=True)
    
    with st.spinner("🔍 Scanning for high-potential patterns..."):
        report_df = generate_market_analysis_report()
    
    if not report_df.empty:
        st.success(f"Found {len(report_df)} stocks matching criteria!")
        
        for idx, row in report_df.iterrows():
            with st.container():
                st.markdown(f"### {row['Name']} ({row['Symbol']})")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Current Price", row['Current Price'])
                col2.metric("RSI", row['RSI'])
                col3.metric("Volume", row['Volume'])
                col4.metric("PE", row['PE'])
                
                st.info(f"🎯 **Suggestion:** {row['Suggestion']} | **Reason:** {row['Reason']}")
                
                # Render pattern chart
                st.plotly_chart(render_pattern_chart(row['df'], row['Symbol']), use_container_width=True)
                st.markdown("---")
    else:
        st.warning("No stocks currently matching the 'Near Lifetime High + Cup & Handle' criteria.")
    
    st.stop()

# Check if we should render ATH breakout report
if st.session_state.get('page_mode') == 'ath_breakout_report':
    with st.sidebar:
        if st.button("← Back to Main Analysis", use_container_width=True):
            st.session_state.page_mode = 'main'
            st.rerun()
    
    st.markdown('<h1 class="main-header">🚀 ATH Breakout Report</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Stocks breaking above 52W and All-Time Highs</p>', unsafe_allow_html=True)
    
    with st.spinner("🔍 Scanning for ATH breakouts..."):
        report_df = generate_ath_breakout_report()
    
    if not report_df.empty:
        st.success(f"Found {len(report_df)} stocks matching criteria!")
        
        for idx, row in report_df.iterrows():
            with st.container():
                st.markdown(f"### {row['Name']} ({row['Symbol']})")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Current Price", row['Current Price'])
                col2.metric("All-Time High", row['All-Time High'])
                col3.metric("Volume", row['Volume'])
                col4.metric("Market Cap (Cr)", row['Market Cap (Cr)'])
                
                st.info(f"🎯 **Suggestion:** {row['Suggestion']} | **Reason:** {row['Reason']}")
                
                # Render chart
                st.plotly_chart(render_ath_chart(row['df'], row['Symbol']), use_container_width=True)
                st.markdown("---")
    else:
        st.warning("No stocks currently matching the 'ATH Breakout' criteria.")
    
    st.stop()

# Check if we should render positional screener
if st.session_state.get('page_mode') == 'positional_screener':
    import json as _json
    from pathlib import Path as _Path

    with st.sidebar:
        if st.button("← Back to Main Analysis", use_container_width=True):
            st.session_state.page_mode = 'main'
            st.session_state.pop('screener_results', None)
            st.rerun()

    st.title("🎯 Positional Screener — NSE 500")
    st.caption("Multi-factor scoring: Trend · Momentum · Fundamentals · Sector Tailwind · Risk:Reward")

    # ── Run Scan button ──────────────────────────────────────────
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        _run_btn = st.button("🔍 Run Scan", type="primary", use_container_width=True,
                             help="Fetch live data and score all 521 NSE 500 stocks")
    with col_info:
        if st.session_state.get('screener_results'):
            _first = st.session_state['screener_results'][0]
            st.info(f"Last scan: {_first.get('scannedAt', '—')}  ·  {len(st.session_state['screener_results'])} stocks scored")
        else:
            st.info("No scan results yet — click **Run Scan** to analyse all NSE 500 stocks with live Yahoo Finance data.")

    if _run_btn:
        _progress_bar  = st.progress(0, text="Starting scan…")
        _status_holder = st.empty()

        def _on_progress(pct, status):
            _progress_bar.progress(min(int(pct), 100) / 100, text=status)
            _status_holder.caption(status)

        _results = _run_scan_direct(progress_cb=_on_progress)
        st.session_state['screener_results'] = _results
        _progress_bar.empty()
        _status_holder.empty()
        st.rerun()

    # ── Render HTML panel with pre-injected data ─────────────────
    _html_path = _Path(__file__).parent / "public" / "index.html"
    _html_template = _html_path.read_text(encoding="utf-8")

    _results_data = st.session_state.get('screener_results', [])
    _alldata_json  = _json.dumps(_results_data, ensure_ascii=False, default=str)
    _html_ready    = _html_template.replace("ALLDATA_PLACEHOLDER", _alldata_json)

    _components.html(_html_ready, height=820, scrolling=True)

    st.stop()

# Check if we should render market report
if st.session_state.get('page_mode') == 'market_report':
    # Add back to main button in sidebar
    with st.sidebar:
        if st.button("← Back to Main Analysis", use_container_width=True):
            st.session_state.page_mode = 'main'
            st.rerun()
    
    st.markdown('<h1 class="main-header">📊 NSE 500 Market Report</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Golden Cross & Death Cross Analysis - Past 7 Days</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        cross_filter = st.selectbox("Filter by Cross Type:", ["All", "Golden Cross", "Death Cross"])
    with col2:
        recommendation_filter = st.selectbox("Filter by Recommendation:", ["All", "BUY", "HOLD", "SELL"])
    with col3:
        if st.button("🔄 Refresh Analysis", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # RSI Information Expander
    with st.expander("📚 Understanding RSI (Relative Strength Index)", expanded=False):
        rsi_info = get_rsi_education()
        st.markdown("**RSI Formula:**")
        st.code(rsi_info['formula'], language="text")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Key Signals:**")
            for signal, description in rsi_info['signals'].items():
                st.markdown(f"- **{signal.replace('_', ' ').title()}**: {description}")
        
        with col2:
            st.markdown("**Divergence Signals:**")
            for div_type, description in rsi_info['divergence'].items():
                st.markdown(f"- **{div_type.title()}**: {description}")
        
        st.markdown("**Limitations (Important!):**")
        for limitation in rsi_info['limitations']:
            st.markdown(f"- {limitation}")
        
        st.info("💡 **Pro Tip**: Use RSI with Moving Averages (MA50/MA200), Support/Resistance levels, and Volume for best results!")
    
    st.markdown("---")
    
    with st.spinner("📊 Analyzing NSE 500 stocks for Golden/Death crosses..."):
        market_data = analyze_nse500_crosses()
    
    if market_data is not None and not market_data.empty:
        filtered_data = filter_results(market_data, cross_filter if cross_filter != "All" else None, 
                                      recommendation_filter if recommendation_filter != "All" else None)
        
        st.markdown(f"### Found {len(filtered_data)} stocks with recent crosses")
        
        # Summary metrics
        gold_count = len(market_data[market_data['Cross Type'] == 'Golden Cross'])
        death_count = len(market_data[market_data['Cross Type'] == 'Death Cross'])
        buy_count = len(market_data[market_data['Recommendation'] == 'BUY'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🟢 Golden Crosses", gold_count)
        with col2:
            st.metric("🔴 Death Crosses", death_count)
        with col3:
            st.metric("💰 Buy Signals", buy_count)
        with col4:
            st.metric("📊 Total Signals", len(market_data))
        
        st.markdown("---")
        
        # Display table
        display_cols = ['Symbol', 'Company Name', 'Cross Type', 'Cross Date', 'Price at Cross', 
                       'Current Price', 'Price Change %', 'RSI', 'P/E Ratio', 'ROI %', 'Divergence', 'Recommendation', 'Reason']
        
        st.dataframe(
            filtered_data[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                'Symbol': st.column_config.TextColumn('📍 Symbol'),
                'Company Name': st.column_config.TextColumn('🏢 Company'),
                'Cross Type': st.column_config.TextColumn('🔄 Cross Type'),
                'Cross Date': st.column_config.TextColumn('📅 Date'),
                'Price at Cross': st.column_config.TextColumn('💰 Price @ Cross'),
                'Current Price': st.column_config.TextColumn('📈 Current Price'),
                'Price Change %': st.column_config.TextColumn('📊 % Change'),
                'RSI': st.column_config.TextColumn('RSI'),
                'P/E Ratio': st.column_config.TextColumn('P/E'),
                'ROI %': st.column_config.TextColumn('ROI'),
                'Divergence': st.column_config.TextColumn('🔀 Divergence'),
                'Recommendation': st.column_config.TextColumn('⭐ Recommendation'),
                'Reason': st.column_config.TextColumn('💡 Reason')
            }
        )
        
        # Download button
        csv_data = filtered_data[display_cols].to_csv(index=False)
        st.download_button(
            label="💾 Download Report as CSV",
            data=csv_data,
            file_name=f"NSE500_Market_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("⚠️ No stocks with recent crosses found. Analyzing...")
    
    st.stop()

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
    
    # Search input and button layout
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Smart search with autocomplete
        search_query = st.text_input(
            "Search stocks...",
            value=st.session_state.search_query,
            placeholder="Type symbol or company name (e.g., RELIANCE, TCS, Infosys)",
            help="Start typing to see suggestions",
            key="search_input",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍", help="Search stocks", use_container_width=True)
    
    # Initialize variables
    selected_stock = None
    full_symbol = None
    
    # Show suggestions when user types or clicks search button
    if (search_query and len(search_query) >= 1) or search_button:
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
    
    # Store period info for display in metrics
    st.session_state.selected_period_label = selected_period
    st.session_state.selected_period = period
    
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
    # Add Market Report and Excel Watchlist navigation
    st.markdown("---")
    st.markdown("### 📊 Market Analysis Reports")
    
    if st.button("🎯 NSE 500 Market Report", use_container_width=True, help="Analyze NSE 500 stocks for Golden/Death crosses in past week"):
        st.session_state.page_mode = 'market_report'
        st.rerun()

    if st.button("🏆 Lifetime High Analysis", use_container_width=True, help="Stocks near lifetime high with Cup & Handle pattern"):
        st.session_state.page_mode = 'lifetime_high_report'
        st.rerun()

    if st.button("🚀 ATH Breakout Analysis", use_container_width=True, help="Stocks breaking above All-Time Highs"):
        st.session_state.page_mode = 'ath_breakout_report'
        st.rerun()

    if st.button("🎯 Positional Screener", use_container_width=True, help="Multi-factor NSE 500 scoring: Trend + Momentum + Fundamentals + Sector + Risk:Reward"):
        st.session_state.page_mode = 'positional_screener'
        st.rerun()
    
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
    
    # Calculate period-specific metrics
    high_period = stock_data['High'].max()
    low_period = stock_data['Low'].min()
    avg_volume = stock_data['Volume'].mean()
    
    # Calculate fixed 1-Year and 5-Year metrics if possible for comparison/consistency
    # We fetch a slightly larger dataset to ensure these are always accurate regardless of selected period
    @st.cache_data(ttl=3600)
    def get_standard_metrics(symbol):
        try:
            full_data = data_fetcher.fetch_stock_data(symbol, "5y")
            if full_data is not None:
                # 1 Year High/Low
                one_year_ago = datetime.now() - timedelta(days=365)
                df_1y = full_data[full_data.index >= one_year_ago]
                h1y = df_1y['High'].max() if not df_1y.empty else full_data['High'].max()
                l1y = df_1y['Low'].min() if not df_1y.empty else full_data['Low'].min()
                
                # 5 Year High/Low
                h5y = full_data['High'].max()
                l5y = full_data['Low'].min()
                
                # Absolute current price (latest available)
                latest_price = full_data['Close'].iloc[-1]
                return h1y, l1y, h5y, l5y, latest_price
        except:
            pass
        return None, None, None, None, None

    h1y, l1y, h5y, l5y, latest_price = get_standard_metrics(symbol)
    
    # Get period label for display
    period_label = st.session_state.get('selected_period_label', '52W')

    # Use standard metrics if available, otherwise fallback to period-based
    display_high = h1y if period_label == "1 Year" else (h5y if "5 Year" in period_label else high_period)
    display_low = l1y if period_label == "1 Year" else (l5y if "5 Year" in period_label else low_period)
    current_price = latest_price if latest_price is not None else stock_data['Close'].iloc[-1]
    
    prev_price = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
    volume_change = ((stock_data['Volume'].iloc[-1] / stock_data['Volume'].iloc[-2] - 1) * 100) if len(stock_data) > 1 else 0
    
    # Price performance metrics
    period_return = ((current_price / stock_data['Close'].iloc[0]) - 1) * 100
    volatility = stock_data['Close'].pct_change().std() * 100
    
    # Calculate RSI
    rsi_value = calculate_rsi(stock_data)
    
    # Detect divergence
    divergence_signal = detect_divergence(stock_data)
    
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
            label=f"📈 {period_label} High",
            value=f"₹{display_high:.2f}",
            help=f"Distance from high: {((current_price/display_high - 1) * 100):.1f}%"
        )
    
    with col4:
        st.metric(
            label=f"📉 {period_label} Low",
            value=f"₹{display_low:.2f}",
            help=f"Distance from low: {((current_price/display_low - 1) * 100):.1f}%"
        )
    
    # Additional metrics row with RSI and Divergence
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
    
    # RSI and Divergence metrics row
    st.markdown("---")
    st.markdown("### 📈 Technical Analysis")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        rsi_display = f"{rsi_value:.2f}" if rsi_value else "N/A"
        rsi_status = ""
        if rsi_value:
            if rsi_value > 70:
                rsi_status = "🔴 Overbought"
            elif rsi_value < 30:
                rsi_status = "🟢 Oversold"
            elif rsi_value > 50:
                rsi_status = "🟢 Bullish"
            else:
                rsi_status = "🔴 Bearish"
        
        st.metric(
            label="📊 RSI (14)",
            value=rsi_display,
            help=f"{rsi_status} - RSI > 70 (Overbought), < 30 (Oversold), > 50 (Bullish), < 50 (Bearish)"
        )
    
    with col2:
        divergence_display = divergence_signal if divergence_signal else "None"
        divergence_color = "🟢" if divergence_signal == "Bullish Divergence" else "🔴" if divergence_signal == "Bearish Divergence" else "⚪"
        
        st.metric(
            label="🔀 Divergence Signal",
            value=f"{divergence_color} {divergence_display}",
            help="Bullish: Price lower low, RSI higher low (Reversal up) | Bearish: Price higher high, RSI lower high (Reversal down)"
        )
    
    with col3:
        # Calculate valuation metrics
        percent_from_high = ((current_price / display_high) - 1) * 100
        percent_from_low = ((current_price / display_low) - 1) * 100
        price_position = ((current_price - display_low) / (display_high - display_low)) * 100 if display_high != display_low else 50
        
        st.metric(
            label="💎 % from 52W High",
            value=f"{percent_from_high:.2f}%",
            help=f"Negative values mean discount from high (better value)"
        )
    
    with col4:
        # Valuation score: 0-100 where higher is better value (lower price in range)
        valuation_score = max(0, min(100, 100 - price_position))
        valuation_label = "🔴 Expensive" if valuation_score < 33 else "🟡 Fair" if valuation_score < 66 else "🟢 Undervalued"
        
        st.metric(
            label="📊 Valuation Score",
            value=f"{valuation_score:.0f}/100 {valuation_label}",
            help="0=Expensive (near high), 100=Undervalued (near low)"
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
    
    # Golden Cross / Death Cross Analysis Section
    st.markdown("### 🔄 Golden Cross & Death Cross Analysis")
    
    st.markdown("""
    <div class="feature-highlight">
        <strong>What is Golden Cross & Death Cross?</strong><br>
        • <strong style="color: #00FF00;">Golden Cross</strong>: When 50-day MA crosses ABOVE 200-day MA (Bullish signal)<br>
        • <strong style="color: #FF0000;">Death Cross</strong>: When 50-day MA crosses BELOW 200-day MA (Bearish signal)
    </div>
    """, unsafe_allow_html=True)
    
    if len(stock_data) >= 200:
        # Detect cross events
        cross_events = detect_golden_death_cross(stock_data)
        
        # Create cross analysis chart
        cross_chart = create_cross_analysis_chart(stock_data, symbol)
        
        if cross_chart is not None:
            st.plotly_chart(cross_chart, use_container_width=True)
        
        # Display cross events table
        if not cross_events.empty:
            st.markdown("#### 📋 Cross Events History")
            
            # Summary metrics
            golden_count = len(cross_events[cross_events['Cross Type'] == 'Golden Cross'])
            death_count = len(cross_events[cross_events['Cross Type'] == 'Death Cross'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="🔼 Golden Crosses",
                    value=golden_count,
                    help="Number of bullish crossover events"
                )
            with col2:
                st.metric(
                    label="🔽 Death Crosses",
                    value=death_count,
                    help="Number of bearish crossover events"
                )
            with col3:
                st.metric(
                    label="📊 Total Events",
                    value=len(cross_events),
                    help="Total number of cross events detected"
                )
            
            # Display the events table with styling
            st.dataframe(
                cross_events,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("📅 Date"),
                    "Cross Type": st.column_config.TextColumn("🔄 Cross Type"),
                    "Close Price": st.column_config.TextColumn("💰 Price at Cross"),
                    "Current Price": st.column_config.TextColumn("📈 Current Price"),
                    "% Change": st.column_config.TextColumn("📊 % Change Since Cross"),
                    "Days Since": st.column_config.NumberColumn("⏱️ Days Ago")
                }
            )
            
            st.markdown("""
            <div class="feature-highlight" style="margin-top: 1rem;">
                <strong>📈 How to Read This Data:</strong><br>
                • <strong>% Change</strong>: Shows how much the price has moved since the cross event<br>
                • <strong>Green values</strong> in % Change indicate price is UP since the cross<br>
                • <strong>Red values</strong> in % Change indicate price is DOWN since the cross<br>
                • <strong>Days Since</strong>: Number of trading days since the event occurred
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("📊 No Golden Cross or Death Cross events detected in the selected period. Try selecting a longer time range (2 Years or 5 Years) to see historical cross events.")
    else:
        st.warning(f"⚠️ Need at least 200 days of data for Golden Cross / Death Cross analysis. Current data has {len(stock_data)} days. Please select a longer time period (2 Years or 5 Years).")
    
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
    
    # Calculate RSI for each row
    rsi_values = []
    for i in range(len(stock_data)):
        if i < 14:  # Need at least 14 periods for RSI
            rsi_values.append(None)
        else:
            data_slice = stock_data.iloc[:i+1]
            rsi = calculate_rsi(data_slice, period=14)
            rsi_values.append(f"{rsi:.2f}" if rsi else "N/A")
    display_data['RSI (14)'] = rsi_values
    
    # Calculate Divergence Signals for each row
    divergence_values = []
    for i in range(len(stock_data)):
        if i < 50:  # Need at least 50 periods for divergence detection
            divergence_values.append(None)
        else:
            data_slice = stock_data.iloc[:i+1]
            divergence = detect_divergence(data_slice)
            divergence_values.append(divergence if divergence else "—")
    display_data['Divergence Signal'] = divergence_values
    
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
    column_order = ['Date', 'Open', 'High', 'Low', 'Close', 'Daily Change (₹)', 'Daily Change (%)', 'RSI (14)', 'Divergence Signal', 'Volume']
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
            "RSI (14)": st.column_config.TextColumn("📈 RSI (14)"),
            "Divergence Signal": st.column_config.TextColumn("🔀 Divergence"),
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
    st.markdown("### 🎯 Screeners & Reports")

    screen_col1, screen_col2, screen_col3, screen_col4 = st.columns(4)

    with screen_col1:
        st.markdown("""
        <div class="stock-card">
            <h3 style="color: #00D4AA;">🎯 Positional Screener</h3>
            <p>Multi-factor scoring across NSE 500 stocks — Trend, Momentum, Fundamentals, Sector, and Risk:Reward.</p>
            <ul style="margin-top: 1rem;">
                <li>100-point composite score</li>
                <li>STRONG BUY / BUY / WATCH</li>
                <li>ATR-based SL &amp; Target</li>
                <li>Detailed breakdown per stock</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎯 Open Positional Screener", key="home_positional", use_container_width=True):
            st.session_state.page_mode = 'positional_screener'
            st.rerun()

    with screen_col2:
        st.markdown("""
        <div class="stock-card">
            <h3 style="color: #7B68EE;">🏆 Lifetime High Report</h3>
            <p>Stocks trading near their all-time highs with Cup &amp; Handle pattern confirmation.</p>
            <ul style="margin-top: 1rem;">
                <li>Within 2% of ATH</li>
                <li>Cup &amp; Handle detection</li>
                <li>RSI momentum check</li>
                <li>Interactive pattern charts</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏆 Open Lifetime High Report", key="home_lifetime", use_container_width=True):
            st.session_state.page_mode = 'lifetime_high_report'
            st.rerun()

    with screen_col3:
        st.markdown("""
        <div class="stock-card">
            <h3 style="color: #FF6B6B;">🚀 ATH Breakout Report</h3>
            <p>Stocks breaking above their 52-week and all-time highs with volume confirmation.</p>
            <ul style="margin-top: 1rem;">
                <li>Price &gt; ATH × 1.1 filter</li>
                <li>Volume &amp; market cap filter</li>
                <li>Breakout confirmation</li>
                <li>Downloadable CSV report</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Open ATH Breakout Report", key="home_ath", use_container_width=True):
            st.session_state.page_mode = 'ath_breakout_report'
            st.rerun()

    with screen_col4:
        st.markdown("""
        <div class="stock-card">
            <h3 style="color: #FFD700;">🎯 NSE 500 Market Report</h3>
            <p>Scan all NSE 500 stocks for Golden Cross and Death Cross signals with RSI divergence.</p>
            <ul style="margin-top: 1rem;">
                <li>Golden / Death Cross scan</li>
                <li>RSI divergence detection</li>
                <li>BUY / HOLD / SELL signals</li>
                <li>Downloadable CSV report</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎯 Open NSE 500 Report", key="home_nse500", use_container_width=True):
            st.session_state.page_mode = 'market_report'
            st.rerun()

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
