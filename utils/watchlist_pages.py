"""
Watchlist pages module for StockScope application
Creates dynamic pages based on Excel file analysis for stock review and portfolio management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.stock_data import StockDataFetcher
from utils.chart_utils import create_price_chart, create_volume_chart
from utils.excel_analyzer import ExcelAnalyzer
from utils.live_data_fetcher import LiveDataFetcher, refresh_live_data
import numpy as np
from datetime import datetime, timedelta

class WatchlistPages:
    """Creates dynamic pages based on Excel watchlist data"""
    
    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.analyzer = ExcelAnalyzer(excel_file_path)
        self.analysis = self.analyzer.analyze_file()
        self.stock_fetcher = st.session_state.get('stock_fetcher')
        self.live_fetcher = LiveDataFetcher()
        
    def render_watchlist_overview(self):
        """Render overview page showing all available watchlists"""
        st.title("📊 Watchlist Overview")
        st.markdown("Review your uploaded Excel file and explore different stock categories")
        
        if 'error' in self.analysis:
            st.error(f"Error reading Excel file: {self.analysis['error']}")
            return
        
        # File summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sheets", len(self.analysis['sheet_names']))
        with col2:
            st.metric("Stock Symbols", len(self.analysis.get('stock_symbols', set())))
        with col3:
            st.metric("Available Categories", len([s for s in self.analysis['sheet_names'] if s not in ['Sheet1', 'Sheet9', 'Table']]))
        with col4:
            st.metric("Data Points", sum(info.get('rows', 0) for info in self.analysis['sheets_info'].values() if 'error' not in info))
        
        st.markdown("---")
        
        # Available watchlists
        st.subheader("Available Stock Categories")
        
        # Create cards for each meaningful sheet
        meaningful_sheets = [name for name in self.analysis['sheet_names'] 
                           if name not in ['Sheet1', 'Sheet9', 'Table'] and 
                           self.analysis['sheets_info'].get(name, {}).get('rows', 0) > 5]
        
        if not meaningful_sheets:
            st.info("No stock categories found in the uploaded file.")
            return

        cols = st.columns(min(3, len(meaningful_sheets)))
        for idx, sheet_name in enumerate(meaningful_sheets):
            col = cols[idx % 3]
            sheet_info = self.analysis['sheets_info'][sheet_name]
            
            with col:
                with st.container():
                    st.markdown(f"""
                    <div style="
                        padding: 1rem;
                        border-radius: 0.5rem;
                        border: 1px solid #333;
                        background: linear-gradient(135deg, #1f1f1f 0%, #2d2d2d 100%);
                        margin-bottom: 1rem;
                        transition: transform 0.2s;
                    ">
                        <h4 style="margin: 0 0 0.5rem 0; color: #00d4ff;">{sheet_name}</h4>
                        <p style="margin: 0; color: #ccc; font-size: 0.9rem;">
                            📈 {sheet_info.get('rows', 0)} stocks<br>
                            📊 {len(sheet_info.get('potential_price_columns', []))} price metrics
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Explore {sheet_name}", key=f"explore_{sheet_name}"):
                        st.session_state.selected_watchlist = sheet_name
                        st.rerun()
    
    def render_sector_watchlist(self, sheet_name: str):
        """Render individual sector/watchlist page"""
        if sheet_name not in self.analysis['sheets_info']:
            st.error(f"Sheet '{sheet_name}' not found")
            return
        
        sheet_info = self.analysis['sheets_info'][sheet_name]
        if 'error' in sheet_info:
            st.error(f"Error reading sheet: {sheet_info['error']}")
            return
        
        # Get sheet data and enhance with live data
        df = self.analyzer.get_sheet_data(sheet_name)
        if df.empty:
            st.warning("No data found in this sheet")
            return
        
        # Add refresh button and auto-refresh functionality
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 Refresh Live Data", key=f"refresh_{sheet_name}"):
                with st.spinner("Fetching live data..."):
                    df = refresh_live_data(df, sheet_name)
                    st.success("Live data updated!")
                    st.rerun()
        
        with col2:
            auto_refresh = st.checkbox("Auto-refresh (5min)", key=f"auto_refresh_{sheet_name}")
            if auto_refresh:
                st.empty()  # Placeholder for auto-refresh logic
        
        with col3:
            st.markdown("📊 **Live market data integration enabled**")
        
        # Enhance data with live information
        df = self.live_fetcher.enhance_excel_data(df, sheet_name)
        
        st.title(f"📈 {sheet_name} Watchlist")
        
        # Back button
        if st.button("← Back to Overview"):
            if 'selected_watchlist' in st.session_state:
                del st.session_state.selected_watchlist
            st.rerun()
        
        # Enhanced statistics with live data
        col1, col2, col3, col4 = st.columns(4)
        try:
            with col1:
                identified_stocks = len(df[df['Stock_Name'].notna()]) if 'Stock_Name' in df.columns else 0
                st.metric("Total Stocks", len(df), delta=f"{identified_stocks} identified")
            
            with col2:
                if 'Live_Price' in df.columns:
                    live_prices = df['Live_Price'].dropna()
                    if len(live_prices) > 0:
                        avg_live_price = live_prices.mean()
                        st.metric("Avg Live Price", f"₹{avg_live_price:.2f}")
                    else:
                        price_cols = [col for col in df.columns if 'price' in str(col).lower() or 'close' in str(col).lower()]
                        if price_cols:
                            avg_price = df[price_cols[0]].dropna().mean()
                            st.metric("Avg Price", f"₹{avg_price:.2f}" if not pd.isna(avg_price) else "N/A")
                else:
                    price_cols = [col for col in df.columns if 'price' in str(col).lower() or 'close' in str(col).lower()]
                    if price_cols:
                        avg_price = df[price_cols[0]].dropna().mean()
                        st.metric("Avg Price", f"₹{avg_price:.2f}" if not pd.isna(avg_price) else "N/A")
            
            with col3:
                if 'Live_Change_Percent' in df.columns:
                    change_data = df['Live_Change_Percent'].dropna()
                    if len(change_data) > 0:
                        positive_movers = len(change_data[change_data > 0])
                        negative_movers = len(change_data[change_data < 0])
                        st.metric("Gainers", positive_movers, delta=f"{negative_movers} losers")
                else:
                    suggestion_col = [col for col in df.columns if 'suggestion' in str(col).lower()]
                    if suggestion_col and len(df[suggestion_col[0]].dropna()) > 0:
                        buy_count = len(df[df[suggestion_col[0]].astype(str).str.contains('BUY', na=False, case=False)])
                        st.metric("Buy Signals", buy_count)
            
            with col4:
                if 'Last_Updated' in df.columns:
                    last_updates = df['Last_Updated'].dropna()
                    last_update = last_updates.iloc[-1] if len(last_updates) > 0 else "Never"
                    st.metric("Last Updated", last_update)
        except Exception as e:
            st.warning(f"Could not load statistics: {str(e)}")
        
        st.markdown("---")
        
        # Analysis tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Table", "📈 Performance Analysis", "🎯 Stock Screening", "📋 Quick Analysis"])
        
        with tab1:
            self._render_data_table(df, sheet_name)
        
        with tab2:
            self._render_performance_analysis(df, sheet_name)
        
        with tab3:
            self._render_stock_screening(df, sheet_name)
        
        with tab4:
            self._render_quick_analysis(df, sheet_name)
    
    def _render_data_table(self, df: pd.DataFrame, sheet_name: str):
        """Render interactive data table with comprehensive live data"""
        st.subheader(f"📊 {sheet_name} Data Table")
        
        # Enhanced filters
        col1, col2, col3, col4 = st.columns(4)
        
        # Create a copy for filtering
        filtered_df = df.copy()
        
        with col1:
            # Suggestion filter if available
            if 'Suggestion' in df.columns and len(df['Suggestion'].dropna()) > 0:
                suggestions = df['Suggestion'].dropna().unique().tolist()
                selected_suggestions = st.multiselect(
                    "🎯 Filter by Suggestion",
                    options=suggestions,
                    default=[]
                )
                if len(selected_suggestions) > 0:
                    filtered_df = filtered_df[filtered_df['Suggestion'].isin(selected_suggestions)].copy()
        
        with col2:
            # RSI filter if available
            if 'RSI' in df.columns and len(df['RSI'].dropna()) > 0:
                rsi_min = st.number_input("RSI Min", value=0, max_value=100)
                rsi_max = st.number_input("RSI Max", value=100, max_value=100)
                mask = (filtered_df['RSI'] >= rsi_min) & (filtered_df['RSI'] <= rsi_max)
                filtered_df = filtered_df.loc[mask.fillna(False)].copy()
        
        with col3:
            # 52-week high filter
            if 'From_52W_High' in df.columns and len(df['From_52W_High'].dropna()) > 0:
                show_value_stocks = st.checkbox("💎 Show value stocks (<-20% from 52w high)")
                if show_value_stocks:
                    mask = filtered_df['From_52W_High'] < -20
                    filtered_df = filtered_df.loc[mask.fillna(False)].copy()
        
        with col4:
            # Stock identification filter
            if 'Stock_Name' in df.columns:
                show_identified_only = st.checkbox("✅ Show identified stocks only")
                if show_identified_only:
                    filtered_df = filtered_df[filtered_df['Stock_Name'].notna()].copy()
        
        # Prepare display dataframe with optimized column ordering (no duplicates)
        # Select core analysis columns in logical order
        display_columns = []
        
        # Core live data columns - prioritized order
        core_columns = [
            'Stock_Name', 'Identified_Symbol', 'Live_Price', 'Live_Change_Percent',
            'Day_High', 'Day_Low', 'High_52W', 'Low_52W', 'From_52W_High',
            'RSI', 'Valuation_Score', 'Divergence_Signal', 
            'Market_Cap_Bucket', 'Industry_Sector',
            'Suggestion', 'Reason', 'Last_Updated'
        ]
        
        for col in core_columns:
            if col in filtered_df.columns:
                display_columns.append(col)
        
        # Exclude duplicate/redundant columns from original data
        exclude_cols = {'Stock Name', 'Price', 'P Close', 'M Cap', 'Industry', 'D Change (%)', 
                       'Live_Change', 'Identified_Symbol', 'Last_Updated', 'Unnamed: 0'}
        
        # Add any other relevant numeric columns (but avoid duplicates)
        for col in filtered_df.columns:
            if col not in display_columns and not any(exc in col for exc in exclude_cols) and not col.startswith('Unnamed'):
                display_columns.append(col)
        
        # Filter to existing columns only
        display_columns = [col for col in display_columns if col in filtered_df.columns]
        display_df = filtered_df[display_columns]
        
        st.markdown(f"**Showing {len(display_df)} of {len(df)} stocks**")
        
        # Enhanced display with comprehensive formatting
        column_config = {}
        
        if 'Stock_Name' in display_df.columns:
            column_config['Stock_Name'] = st.column_config.TextColumn("🏢 Company", width="medium")
        if 'Identified_Symbol' in display_df.columns:
            column_config['Identified_Symbol'] = st.column_config.TextColumn("📊 Symbol", width="small")
        if 'Live_Price' in display_df.columns:
            column_config['Live_Price'] = st.column_config.NumberColumn("💰 Live Price", format="₹%.2f")
        if 'Live_Change_Percent' in display_df.columns:
            column_config['Live_Change_Percent'] = st.column_config.NumberColumn("📊 Change %", format="%.2f%%")
        if 'Day_High' in display_df.columns:
            column_config['Day_High'] = st.column_config.NumberColumn("📈 Day High", format="₹%.2f")
        if 'Day_Low' in display_df.columns:
            column_config['Day_Low'] = st.column_config.NumberColumn("📉 Day Low", format="₹%.2f")
        if 'High_52W' in display_df.columns:
            column_config['High_52W'] = st.column_config.NumberColumn("📊 52w High", format="₹%.2f")
        if 'Low_52W' in display_df.columns:
            column_config['Low_52W'] = st.column_config.NumberColumn("📊 52w Low", format="₹%.2f")
        if 'From_52W_High' in display_df.columns:
            column_config['From_52W_High'] = st.column_config.NumberColumn("📉 % from High", format="%.2f%%")
        if 'RSI' in display_df.columns:
            column_config['RSI'] = st.column_config.NumberColumn("📈 RSI (14)", format="%.2f")
        if 'Valuation_Score' in display_df.columns:
            column_config['Valuation_Score'] = st.column_config.NumberColumn("💎 Valuation", format="%.0f/100")
        if 'Divergence_Signal' in display_df.columns:
            column_config['Divergence_Signal'] = st.column_config.TextColumn("🔀 Divergence", width="small")
        if 'Market_Cap_Bucket' in display_df.columns:
            column_config['Market_Cap_Bucket'] = st.column_config.TextColumn("🏪 Market Cap", width="small")
        if 'Industry_Sector' in display_df.columns:
            column_config['Industry_Sector'] = st.column_config.TextColumn("🏭 Sector", width="medium")
        if 'Suggestion' in display_df.columns:
            column_config['Suggestion'] = st.column_config.TextColumn("⭐ Suggestion", width="small")
        if 'Reason' in display_df.columns:
            column_config['Reason'] = st.column_config.TextColumn("💡 Reason & Details", width="large")
        if 'Last_Updated' in display_df.columns:
            column_config['Last_Updated'] = st.column_config.TextColumn("🕐 Updated", width="small")
        
        # Display enhanced table
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500,
            column_config=column_config,
            hide_index=True
        )
        
        # Export functionality with enhanced data
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export Filtered Data", key=f"export_{sheet_name}"):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{sheet_name}_enhanced_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key=f"download_{sheet_name}"
                )
        
        with col2:
            if 'Stock_Name' in display_df.columns:
                identified_count = len(display_df[display_df['Stock_Name'].notna()])
                st.info(f"📊 {identified_count} stocks identified with live data")
    
    def _render_performance_analysis(self, df: pd.DataFrame, sheet_name: str):
        """Render performance analysis charts"""
        st.subheader(f"📈 {sheet_name} Performance Analysis")
        
        # Find relevant columns
        price_col = None
        change_col = None
        high_col = None
        low_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'price' in col_lower and not price_col:
                price_col = col
            elif 'change' in col_lower and '%' in col_lower and not change_col:
                change_col = col
            elif 'high' in col_lower and '52' in col and not high_col:
                high_col = col
            elif 'low' in col_lower and '52' in col and not low_col:
                low_col = col
        
        if not any([price_col, change_col]):
            st.warning("No suitable price or change data found for analysis")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            if change_col:
                # Price change distribution
                fig = px.histogram(
                    df.dropna(subset=[change_col]),
                    x=change_col,
                    title=f"Price Change Distribution - {sheet_name}",
                    color_discrete_sequence=['#00d4ff']
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if price_col:
                # Price distribution
                fig = px.box(
                    df.dropna(subset=[price_col]),
                    y=price_col,
                    title=f"Price Distribution - {sheet_name}",
                    color_discrete_sequence=['#ff6b6b']
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Enhanced live data analysis
        if 'Live_Price' in df.columns and not df['Live_Price'].isna().all():
            st.subheader("📊 Live Market Analysis")
            
            # Live vs Excel price comparison
            price_comparison_df = df[['Live_Price', price_col]].dropna()
            if not price_comparison_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.scatter(
                        price_comparison_df,
                        x=price_col,
                        y='Live_Price',
                        title="Live Price vs Excel Price",
                        labels={price_col: "Excel Price", 'Live_Price': "Live Price"}
                    )
                    fig.add_trace(go.Scatter(
                        x=[price_comparison_df[price_col].min(), price_comparison_df[price_col].max()],
                        y=[price_comparison_df[price_col].min(), price_comparison_df[price_col].max()],
                        mode='lines',
                        name='Perfect Match',
                        line=dict(dash='dash', color='red')
                    ))
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if 'Live_Change_Percent' in df.columns:
                        live_changes = df['Live_Change_Percent'].dropna()
                        fig = px.histogram(
                            live_changes,
                            title="Live Price Change Distribution",
                            nbins=20,
                            color_discrete_sequence=['#00d4ff']
                        )
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font_color='white'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        # Sector/Industry analysis if available
        sector_col = [col for col in df.columns if 'sector' in col.lower() or 'industry' in col.lower()]
        if len(sector_col) > 0 and price_col is not None:
            st.subheader("Sector-wise Analysis")
            sector_data = df.groupby(sector_col[0])[price_col].agg(['mean', 'count']).reset_index()
            sector_data = sector_data[sector_data['count'] >= 2]  # Only sectors with 2+ stocks
            
            if len(sector_data) > 0:
                fig = px.bar(
                    sector_data.head(10),
                    x=sector_col[0],
                    y='mean',
                    title="Average Price by Sector/Industry",
                    color='mean',
                    color_continuous_scale='viridis'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    xaxis_tickangle=45
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_stock_screening(self, df: pd.DataFrame, sheet_name: str):
        """Render stock screening functionality"""
        st.subheader(f"🎯 {sheet_name} Stock Screening")
        
        # Find numeric columns for screening
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            st.warning("No numeric columns found for screening")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Set Screening Criteria:**")
            
            # Price range filter
            price_cols = [col for col in numeric_cols if 'price' in col.lower()]
            if price_cols:
                price_col = st.selectbox("Select Price Column", price_cols)
                price_min, price_max = st.slider(
                    f"Price Range (₹)",
                    min_value=float(df[price_col].min()),
                    max_value=float(df[price_col].max()),
                    value=(float(df[price_col].min()), float(df[price_col].max()))
                )
            
            # Change filter
            change_cols = [col for col in numeric_cols if 'change' in col.lower()]
            if change_cols:
                change_col = st.selectbox("Select Change Column", change_cols)
                change_min = st.number_input(f"Minimum Change (%)", value=-100.0)
                change_max = st.number_input(f"Maximum Change (%)", value=100.0)
        
        with col2:
            st.write("**Additional Filters:**")
            
            # Market cap filter
            mcap_cols = [col for col in df.columns if 'cap' in col.lower() and df[col].dtype == 'object']
            if mcap_cols:
                mcap_col = st.selectbox("Market Cap Category", ['All'] + df[mcap_cols[0]].dropna().unique().tolist())
            
            # Suggestion filter
            suggestion_cols = [col for col in df.columns if 'suggestion' in col.lower()]
            if suggestion_cols:
                suggestion_filter = st.selectbox("Suggestion", ['All'] + df[suggestion_cols[0]].dropna().unique().tolist())
        
        # Apply filters
        filtered_df = df.copy()
        
        # Initialize variables with defaults
        price_col = price_cols[0] if price_cols else None
        change_col = change_cols[0] if change_cols else None
        mcap_col = mcap_cols[0] if mcap_cols else None
        
        # Get filter values with defaults
        if price_col is not None and len(df[price_col].dropna()) > 0:
            price_min = st.session_state.get('price_min', float(df[price_col].min()))
            price_max = st.session_state.get('price_max', float(df[price_col].max()))
            mask = (filtered_df[price_col] >= price_min) & (filtered_df[price_col] <= price_max)
            filtered_df = filtered_df.loc[mask].copy()
        
        if change_col is not None and len(df[change_col].dropna()) > 0:
            change_min = st.session_state.get('change_min', -100.0)
            change_max = st.session_state.get('change_max', 100.0)
            mask = (filtered_df[change_col] >= change_min) & (filtered_df[change_col] <= change_max)
            filtered_df = filtered_df.loc[mask].copy()
        
        if len(mcap_cols) > 0:
            mcap_filter = st.session_state.get('mcap_filter', 'All')
            if mcap_filter != 'All':
                mask = filtered_df[mcap_cols[0]] == mcap_filter
                filtered_df = filtered_df.loc[mask].copy()
        
        if len(suggestion_cols) > 0:
            suggestion_filter = st.session_state.get('suggestion_filter', 'All')
            if suggestion_filter != 'All':
                mask = filtered_df[suggestion_cols[0]] == suggestion_filter
                filtered_df = filtered_df.loc[mask].copy()
        
        st.write(f"**Found {len(filtered_df)} stocks matching criteria:**")
        st.dataframe(filtered_df, use_container_width=True)
    
    def _render_quick_analysis(self, df: pd.DataFrame, sheet_name: str):
        """Render quick analysis with technical and valuation metrics"""
        st.subheader(f"📋 {sheet_name} Technical & Valuation Analysis")
        
        # Summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Signal Distribution:**")
            
            # Find suggestion column
            suggestion_col = [col for col in df.columns if 'suggestion' in col.lower()]
            if len(suggestion_col) > 0:
                suggestion_counts = df[suggestion_col[0]].value_counts()
                for signal, count in suggestion_counts.items():
                    percentage = (count / len(df)) * 100
                    st.write(f"• {signal}: {count} stocks ({percentage:.1f}%)")
            
            st.write("\n**Valuation Metrics:**")
            # Add valuation analysis
            price_cols = [col for col in df.columns if 'price' in str(col).lower()]
            high_cols = [col for col in df.columns if '52' in str(col).lower() and 'high' in str(col).lower()]
            
            if len(price_cols) > 0 and len(high_cols) > 0:
                try:
                    price_col = price_cols[0]
                    high_col = high_cols[0]
                    current_prices = df[price_col].dropna()
                    high_prices = df[high_col].dropna()
                    
                    if len(current_prices) > 0 and len(high_prices) > 0:
                        discount_from_high = 100 * (1 - (current_prices / high_prices)).mean()
                        st.write(f"• Avg discount from 52w high: {discount_from_high:.2f}%")
                        
                        value_stocks = len(df[(df[price_col] < df[high_col] * 0.8)])
                        st.write(f"• Undervalued stocks (<80% of 52w high): {value_stocks}")
                except:
                    pass
            
            # Market cap distribution
            mcap_col = [col for col in df.columns if 'cap' in col.lower() and str(df[col].dtype) in ['object', 'float64', 'int64']]
            if len(mcap_col) > 0:
                mcap_counts = df[mcap_col[0]].value_counts()
                st.write(f"\n{mcap_col[0]} Distribution:")
                for cap, count in mcap_counts.items():
                    percentage = (count / len(df)) * 100
                    st.write(f"• {cap}: {count} stocks ({percentage:.1f}%)")
        
        with col2:
            st.write("**Key Insights:**")
            
            # Find numeric columns for insights
            price_col = None
            change_col = None
            
            for col in df.columns:
                try:
                    if 'price' in col.lower() and str(df[col].dtype) in ['float64', 'int64']:
                        price_col = col
                        break
                except:
                    continue
            
            for col in df.columns:
                try:
                    if 'change' in col.lower() and '%' in str(col) and str(df[col].dtype) in ['float64', 'int64']:
                        change_col = col
                        break
                except:
                    continue
            
            if price_col:
                avg_price = df[price_col].mean()
                st.write(f"• Average Price: ₹{avg_price:.2f}")
                
                high_price_stocks = len(df[df[price_col] > avg_price * 1.5])
                st.write(f"• High-priced stocks (>150% avg): {high_price_stocks}")
            
            if change_col:
                positive_change = len(df[df[change_col] > 0])
                negative_change = len(df[df[change_col] < 0])
                st.write(f"• Positive performers: {positive_change}")
                st.write(f"• Negative performers: {negative_change}")
                
                if positive_change > 0:
                    try:
                        best_idx = df[change_col].idxmax()
                        best_performer = df.loc[best_idx]
                        stock_name_col = [col for col in df.columns if 'name' in col.lower()]
                        if len(stock_name_col) > 0:
                            name_val = best_performer[stock_name_col[0]]
                            change_val = best_performer[change_col]
                            st.write(f"• Best performer: {name_val} ({change_val:.2f}%)")
                    except:
                        pass
        
        # Top performers table
        if change_col:
            st.subheader("🏆 Top Performers")
            top_performers = df.nlargest(5, change_col)
            display_cols = [col for col in df.columns if col in ['Stock Name', change_col, price_col, 'Suggestion']]
            display_cols = [col for col in display_cols if col is not None]
            
            if display_cols:
                st.dataframe(top_performers[display_cols], use_container_width=True)

def render_watchlist_navigation():
    """Render navigation for watchlist pages with CSV support"""
    
    # Try different file formats (prioritize Nifty v2)
    files_to_try = [
        "attached_assets/Nifty_watchlist_v2_1766847674173.xlsm",
        "attached_assets/Nifty_watchlist_1753452068694.xlsm",
        "attached_assets/Holding_watchlist_All_stock_1766847674176.csv"
    ]
    
    excel_file_path = None
    for file_path in files_to_try:
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
                if df is not None and len(df) > 0:
                    excel_file_path = file_path
                    break
            else:
                df = pd.read_excel(file_path)
                if df is not None and len(df) > 0:
                    excel_file_path = file_path
                    break
        except Exception as load_err:
            continue
    
    if excel_file_path is None:
        st.error("No watchlist file found. Please upload an Excel or CSV file.")
        return
    
    try:
        watchlist_pages = WatchlistPages(excel_file_path)
        
        # Check if a specific watchlist is selected
        if 'selected_watchlist' in st.session_state and st.session_state.selected_watchlist:
            try:
                watchlist_pages.render_sector_watchlist(st.session_state.selected_watchlist)
            except Exception as render_err:
                st.error(f"Error displaying watchlist: {str(render_err)}")
        else:
            try:
                watchlist_pages.render_watchlist_overview()
            except Exception as overview_err:
                st.error(f"Error loading watchlist overview: {str(overview_err)}")
            
    except Exception as e:
        st.error(f"Error loading watchlist data: {str(e)}")
        import traceback
        st.write(traceback.format_exc())