# StockScope - Advanced Indian Stock Market Analysis App

## Overview

StockScope is a modern, feature-rich Streamlit web application for comprehensive Indian stock market analysis. The app provides intelligent stock search with autocomplete, interactive charts, technical analysis, and advanced data visualization for Indian stocks listed on NSE and BSE. Enhanced with a contemporary dark theme and intuitive user interface following current design trends.

## Recent Changes (Latest Update)

✅ **Modern UI Redesign** - Complete visual overhaul with contemporary styling  
✅ **Smart Search System** - Intelligent autocomplete with 70+ Indian stocks database  
✅ **Sector-based Browsing** - Browse stocks by business sectors  
✅ **Enhanced Metrics** - Additional performance indicators and analytics  
✅ **Improved Data Table** - Enhanced historical data explorer with column formatting  
✅ **Welcome Screen Redesign** - Modern landing page with feature showcase  

## User Preferences

Preferred communication style: Simple, everyday language.
Design preference: Modern, attractive UI following current trends with smart autocomplete functionality.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Frontend**: Streamlit web framework providing an interactive web interface
- **Data Layer**: Yahoo Finance API integration through yfinance library
- **Visualization Layer**: Plotly for interactive charts and graphs
- **Utility Modules**: Modular utility functions for data fetching and chart creation

## Key Components

### Main Application (app.py)
- **Purpose**: Main entry point and UI orchestration
- **Responsibilities**: 
  - Page configuration and layout management
  - Session state management for user interactions
  - Sidebar controls for stock selection and filtering
  - Integration of data fetching and visualization components

### Stock Data Fetcher (utils/stock_data.py)
- **Purpose**: Handles all stock data retrieval operations
- **Key Features**:
  - Automatic symbol variation handling (.NS for NSE, .BO for BSE)
  - Robust error handling for different stock symbol formats
  - Caching mechanism for improved performance
  - Support for multiple time periods (1mo, 3mo, 6mo, 1y, 2y, 5y)

### Chart Utilities (utils/chart_utils.py)
- **Purpose**: Creates interactive financial charts
- **Chart Types Supported**:
  - Candlestick charts for OHLC data
  - Line charts for price trends
  - Volume charts for trading activity
- **Features**: 
  - Customizable chart styling with Indian market-friendly colors
  - Subplot integration for price and volume data
  - Interactive Plotly visualizations

## Data Flow

1. **User Input**: User enters stock symbol or company name through sidebar
2. **Symbol Processing**: StockDataFetcher automatically tries different symbol variations (.NS, .BO)
3. **Data Retrieval**: Yahoo Finance API fetches historical stock data
4. **Data Validation**: System ensures data quality and completeness
5. **Visualization**: Chart utilities generate interactive Plotly charts
6. **Display**: Streamlit renders the complete analysis interface

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for the user interface
- **yfinance**: Yahoo Finance API wrapper for stock data retrieval
- **Plotly**: Interactive charting library for financial visualizations
- **Pandas**: Data manipulation and analysis

### Data Source
- **Yahoo Finance**: Primary data provider for Indian stock market data
- **Exchanges Supported**: NSE (.NS suffix) and BSE (.BO suffix)

## Deployment Strategy

### Architecture Decisions
- **Stateful Session Management**: Uses Streamlit's session state to maintain user selections and cached data
- **Resource Caching**: Implements `@st.cache_resource` decorator for the data fetcher to improve performance
- **Modular Design**: Separates concerns into utility modules for maintainability

### Performance Optimizations
- **Caching Strategy**: Data fetcher instance is cached to avoid repeated initializations
- **Symbol Variation Logic**: Intelligent handling of Indian stock symbols reduces API calls
- **Error Handling**: Graceful fallback mechanisms for failed data requests

### Scalability Considerations
- **Modular Architecture**: Easy to extend with new chart types or data sources
- **Clean Separation**: UI, data, and visualization layers are decoupled
- **Configuration Management**: Centralized page configuration for easy customization

The application is designed to be lightweight, user-friendly, and specifically optimized for Indian stock market analysis with robust symbol handling and interactive visualizations.