"""
Excel file analyzer for StockScope application
Analyzes uploaded Excel files to extract structure, columns, and data for creating dynamic review pages
"""

import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class ExcelAnalyzer:
    """Analyzes Excel files to extract structure and create dynamic pages"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.sheets_data = {}
        self.analysis_results = {}
        
    def analyze_file(self) -> Dict[str, Any]:
        """Analyze the Excel file and return comprehensive structure information"""
        try:
            # Read all sheets from the Excel file
            excel_file = pd.ExcelFile(self.file_path)
            
            analysis = {
                'file_name': self.file_path.split('/')[-1],
                'sheet_names': excel_file.sheet_names,
                'sheets_info': {},
                'suggested_pages': [],
                'stock_symbols': set(),
                'data_types': {}
            }
            
            # Analyze each sheet
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                    sheet_info = self._analyze_sheet(df, sheet_name)
                    analysis['sheets_info'][sheet_name] = sheet_info
                    self.sheets_data[sheet_name] = df
                    
                    # Extract stock symbols
                    symbols = self._extract_stock_symbols(df)
                    analysis['stock_symbols'].update(symbols)
                    
                except Exception as e:
                    logger.warning(f"Could not read sheet '{sheet_name}': {str(e)}")
                    analysis['sheets_info'][sheet_name] = {'error': str(e)}
            
            # Generate page suggestions based on analysis
            analysis['suggested_pages'] = self._generate_page_suggestions(analysis)
            
            self.analysis_results = analysis
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Excel file: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Analyze individual sheet structure and content"""
        info = {
            'name': sheet_name,
            'rows': len(df),
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'data_types': {},
            'sample_data': {},
            'numeric_columns': [],
            'text_columns': [],
            'potential_stock_columns': [],
            'potential_price_columns': [],
            'potential_date_columns': []
        }
        
        # Analyze each column
        for col in df.columns:
            if col in df.columns:
                col_data = df[col].dropna()
                
                # Data type analysis
                info['data_types'][col] = str(df[col].dtype)
                
                # Sample data (first few non-null values)
                sample_values = col_data.head(3).tolist()
                info['sample_data'][col] = sample_values
                
                # Categorize columns based on content
                if df[col].dtype in ['int64', 'float64']:
                    info['numeric_columns'].append(col)
                    
                    # Check if it looks like price data
                    if any(keyword in col.lower() for keyword in ['price', 'value', 'amount', 'rs', 'inr', 'cost']):
                        info['potential_price_columns'].append(col)
                        
                elif df[col].dtype == 'object':
                    info['text_columns'].append(col)
                    
                    # Check if it looks like stock symbols
                    if any(keyword in col.lower() for keyword in ['symbol', 'stock', 'ticker', 'code', 'nse', 'bse']):
                        info['potential_stock_columns'].append(col)
                    
                    # Check if it looks like dates
                    elif any(keyword in col.lower() for keyword in ['date', 'time', 'day', 'month', 'year']):
                        info['potential_date_columns'].append(col)
        
        return info
    
    def _extract_stock_symbols(self, df: pd.DataFrame) -> set:
        """Extract potential stock symbols from the dataframe"""
        symbols = set()
        
        # Look for columns that might contain stock symbols
        potential_symbol_columns = []
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in ['symbol', 'stock', 'ticker', 'code', 'nse', 'bse', 'name']):
                potential_symbol_columns.append(col)
        
        # If no obvious symbol columns, check all text columns
        if not potential_symbol_columns:
            potential_symbol_columns = [col for col in df.columns if df[col].dtype == 'object']
        
        # Extract symbols from identified columns
        for col in potential_symbol_columns:
            col_values = df[col].dropna().astype(str)
            for value in col_values:
                # Clean and validate potential stock symbols
                cleaned_value = str(value).strip().upper()
                
                # Basic validation for Indian stock symbols
                if 2 <= len(cleaned_value) <= 20 and cleaned_value.replace('.', '').replace('-', '').isalnum():
                    symbols.add(cleaned_value)
        
        return symbols
    
    def _generate_page_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions for new pages based on Excel analysis"""
        suggestions = []
        
        for sheet_name, sheet_info in analysis['sheets_info'].items():
            if 'error' in sheet_info:
                continue
                
            # Watchlist page suggestion
            if sheet_info['potential_stock_columns']:
                suggestions.append({
                    'page_type': 'watchlist',
                    'title': f"{sheet_name} Watchlist",
                    'description': f"Review and analyze stocks from {sheet_name}",
                    'sheet_name': sheet_name,
                    'stock_columns': sheet_info['potential_stock_columns'],
                    'price_columns': sheet_info['potential_price_columns'],
                    'features': ['stock_analysis', 'comparison', 'performance_tracking']
                })
            
            # Portfolio analysis page
            if sheet_info['potential_price_columns'] and sheet_info['potential_stock_columns']:
                suggestions.append({
                    'page_type': 'portfolio',
                    'title': f"{sheet_name} Portfolio Analysis",
                    'description': f"Detailed portfolio analysis based on {sheet_name} data",
                    'sheet_name': sheet_name,
                    'stock_columns': sheet_info['potential_stock_columns'],
                    'price_columns': sheet_info['potential_price_columns'],
                    'features': ['portfolio_value', 'profit_loss', 'allocation']
                })
            
            # Data table review page
            suggestions.append({
                'page_type': 'data_review',
                'title': f"{sheet_name} Data Review",
                'description': f"Interactive data table for {sheet_name}",
                'sheet_name': sheet_name,
                'all_columns': sheet_info['columns'],
                'features': ['filtering', 'sorting', 'export']
            })
        
        return suggestions
    
    def get_sheet_data(self, sheet_name: str) -> pd.DataFrame:
        """Get data for a specific sheet"""
        return self.sheets_data.get(sheet_name, pd.DataFrame())
    
    def get_stock_symbols_list(self) -> List[str]:
        """Get list of all extracted stock symbols"""
        if not self.analysis_results:
            return []
        return sorted(list(self.analysis_results.get('stock_symbols', set())))
    
    def create_summary_report(self) -> Dict[str, Any]:
        """Create a summary report of the Excel file analysis"""
        if not self.analysis_results:
            return {}
        
        total_stocks = len(self.analysis_results.get('stock_symbols', set()))
        total_sheets = len(self.analysis_results.get('sheet_names', []))
        suggested_pages_count = len(self.analysis_results.get('suggested_pages', []))
        
        return {
            'file_name': self.analysis_results.get('file_name', 'Unknown'),
            'total_sheets': total_sheets,
            'total_stocks_found': total_stocks,
            'suggested_pages_count': suggested_pages_count,
            'sheet_summaries': {
                name: {
                    'rows': info.get('rows', 0),
                    'columns': info.get('column_count', 0),
                    'has_stocks': len(info.get('potential_stock_columns', [])) > 0,
                    'has_prices': len(info.get('potential_price_columns', [])) > 0
                }
                for name, info in self.analysis_results.get('sheets_info', {}).items()
                if 'error' not in info
            }
        }

@st.cache_data
def analyze_excel_file(file_path: str):
    """Cached function to analyze Excel file"""
    analyzer = ExcelAnalyzer(file_path)
    return analyzer.analyze_file(), analyzer

def display_excel_analysis_summary(analysis: Dict[str, Any]):
    """Display a summary of Excel analysis results in Streamlit"""
    if 'error' in analysis:
        st.error(f"Error analyzing file: {analysis['error']}")
        return
    
    st.subheader("📊 Excel File Analysis")
    
    # File overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sheets", len(analysis['sheet_names']))
    with col2:
        st.metric("Stock Symbols Found", len(analysis['stock_symbols']))
    with col3:
        st.metric("Suggested Pages", len(analysis['suggested_pages']))
    
    # Sheets overview
    st.subheader("📋 Sheets Overview")
    for sheet_name, sheet_info in analysis['sheets_info'].items():
        if 'error' in sheet_info:
            st.warning(f"⚠️ Could not read sheet '{sheet_name}': {sheet_info['error']}")
            continue
            
        with st.expander(f"📄 {sheet_name} ({sheet_info['rows']} rows, {sheet_info['column_count']} columns)"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Columns:**")
                for col in sheet_info['columns'][:10]:  # Show first 10 columns
                    st.write(f"• {col}")
                if len(sheet_info['columns']) > 10:
                    st.write(f"... and {len(sheet_info['columns']) - 10} more")
            
            with col2:
                if sheet_info['potential_stock_columns']:
                    st.write("**Stock Columns:**")
                    for col in sheet_info['potential_stock_columns']:
                        st.write(f"📈 {col}")
                
                if sheet_info['potential_price_columns']:
                    st.write("**Price Columns:**")
                    for col in sheet_info['potential_price_columns']:
                        st.write(f"💰 {col}")
    
    # Page suggestions
    if analysis['suggested_pages']:
        st.subheader("💡 Suggested New Pages")
        for i, suggestion in enumerate(analysis['suggested_pages']):
            st.write(f"**{i+1}. {suggestion['title']}**")
            st.write(f"   {suggestion['description']}")
            st.write(f"   Features: {', '.join(suggestion['features'])}")