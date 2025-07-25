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
import numpy as np
from datetime import datetime, timedelta

class WatchlistPages:
    """Creates dynamic pages based on Excel watchlist data"""
    
    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.analyzer = ExcelAnalyzer(excel_file_path)
        self.analysis = self.analyzer.analyze_file()
        self.stock_fetcher = st.session_state.get('stock_fetcher')
        
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
        
        # Get sheet data
        df = self.analyzer.get_sheet_data(sheet_name)
        if df.empty:
            st.warning("No data found in this sheet")
            return
        
        st.title(f"📈 {sheet_name} Watchlist")
        
        # Back button
        if st.button("← Back to Overview"):
            if 'selected_watchlist' in st.session_state:
                del st.session_state.selected_watchlist
            st.rerun()
        
        # Sheet statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Stocks", len(df))
        with col2:
            price_cols = [col for col in df.columns if 'price' in col.lower() or 'close' in col.lower()]
            if price_cols:
                avg_price = df[price_cols[0]].dropna().mean()
                st.metric("Avg Price", f"₹{avg_price:.2f}" if not pd.isna(avg_price) else "N/A")
        with col3:
            suggestion_col = [col for col in df.columns if 'suggestion' in col.lower()]
            if suggestion_col:
                buy_signals = len(df[df[suggestion_col[0]].str.contains('BUY', na=False)])
                st.metric("Buy Signals", buy_signals)
        
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
        """Render interactive data table"""
        st.subheader(f"📊 {sheet_name} Data Table")
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            # Suggestion filter if available
            suggestion_col = [col for col in df.columns if 'suggestion' in col.lower()]
            if suggestion_col:
                suggestions = df[suggestion_col[0]].dropna().unique()
                selected_suggestions = st.multiselect(
                    "Filter by Suggestion",
                    options=suggestions,
                    default=[]
                )
                if selected_suggestions:
                    mask = df[suggestion_col[0]].isin(selected_suggestions)
                    df = df.loc[mask].copy()
        
        with col2:
            # Market cap filter if available
            mcap_col = [col for col in df.columns if 'cap' in col.lower() and col != 'M Cap']
            if mcap_col:
                mcap_categories = df[mcap_col[0]].dropna().unique()
                selected_mcap = st.multiselect(
                    "Filter by Market Cap",
                    options=mcap_categories,
                    default=[]
                )
                if selected_mcap:
                    mask = df[mcap_col[0]].isin(selected_mcap)
                    df = df.loc[mask].copy()
        
        # Display table
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )
        
        # Export functionality
        if st.button("📥 Export Filtered Data"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{sheet_name}_filtered_data.csv",
                mime="text/csv"
            )
    
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
        
        # Sector/Industry analysis if available
        sector_col = [col for col in df.columns if 'sector' in col.lower() or 'industry' in col.lower()]
        if sector_col and price_col:
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
        if price_col and not df[price_col].empty:
            price_min = st.session_state.get('price_min', float(df[price_col].min()))
            price_max = st.session_state.get('price_max', float(df[price_col].max()))
            mask = (filtered_df[price_col] >= price_min) & (filtered_df[price_col] <= price_max)
            filtered_df = filtered_df.loc[mask].copy()
        
        if change_col and not df[change_col].empty:
            change_min = st.session_state.get('change_min', -100.0)
            change_max = st.session_state.get('change_max', 100.0)
            mask = (filtered_df[change_col] >= change_min) & (filtered_df[change_col] <= change_max)
            filtered_df = filtered_df.loc[mask].copy()
        
        if mcap_cols:
            mcap_filter = st.session_state.get('mcap_filter', 'All')
            if mcap_filter != 'All':
                mask = filtered_df[mcap_cols[0]] == mcap_filter
                filtered_df = filtered_df.loc[mask].copy()
        
        if suggestion_cols:
            suggestion_filter = st.session_state.get('suggestion_filter', 'All')
            if suggestion_filter != 'All':
                mask = filtered_df[suggestion_cols[0]] == suggestion_filter
                filtered_df = filtered_df.loc[mask].copy()
        
        st.write(f"**Found {len(filtered_df)} stocks matching criteria:**")
        st.dataframe(filtered_df, use_container_width=True)
    
    def _render_quick_analysis(self, df: pd.DataFrame, sheet_name: str):
        """Render quick analysis and insights"""
        st.subheader(f"📋 {sheet_name} Quick Analysis")
        
        # Summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Portfolio Summary:**")
            
            # Find suggestion column
            suggestion_col = [col for col in df.columns if 'suggestion' in col.lower()]
            if suggestion_col:
                suggestion_counts = df[suggestion_col[0]].value_counts()
                st.write("Signal Distribution:")
                for signal, count in suggestion_counts.items():
                    percentage = (count / len(df)) * 100
                    st.write(f"• {signal}: {count} stocks ({percentage:.1f}%)")
            
            # Market cap distribution
            mcap_col = [col for col in df.columns if 'cap' in col.lower() and df[col].dtype == 'object']
            if mcap_col:
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
                if 'price' in col.lower() and df[col].dtype in ['float64', 'int64']:
                    price_col = col
                    break
            
            for col in df.columns:
                if 'change' in col.lower() and '%' in col and df[col].dtype in ['float64', 'int64']:
                    change_col = col
                    break
            
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
                    best_performer = df.loc[df[change_col].idxmax()]
                    stock_name_col = [col for col in df.columns if 'name' in col.lower()]
                    if stock_name_col:
                        st.write(f"• Best performer: {best_performer[stock_name_col[0]]} ({best_performer[change_col]:.2f}%)")
        
        # Top performers table
        if change_col:
            st.subheader("🏆 Top Performers")
            top_performers = df.nlargest(5, change_col)
            display_cols = [col for col in df.columns if col in ['Stock Name', change_col, price_col, 'Suggestion']]
            display_cols = [col for col in display_cols if col is not None]
            
            if display_cols:
                st.dataframe(top_performers[display_cols], use_container_width=True)

def render_watchlist_navigation():
    """Render navigation for watchlist pages"""
    
    # Initialize watchlist pages
    excel_file_path = "attached_assets/Nifty_watchlist_1753452068694.xlsm"
    
    try:
        watchlist_pages = WatchlistPages(excel_file_path)
        
        # Check if a specific watchlist is selected
        if 'selected_watchlist' in st.session_state:
            watchlist_pages.render_sector_watchlist(st.session_state.selected_watchlist)
        else:
            watchlist_pages.render_watchlist_overview()
            
    except Exception as e:
        st.error(f"Error loading watchlist data: {str(e)}")
        st.info("Please ensure the Excel file is properly uploaded and accessible.")