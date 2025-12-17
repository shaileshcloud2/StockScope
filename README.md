# StockScope - Indian Stock Market Analysis

A comprehensive, feature-rich web application for analyzing Indian stocks listed on NSE and BSE exchanges. Built with Streamlit and powered by real-time data from Yahoo Finance.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

### Smart Stock Search
- Intelligent autocomplete with 70+ Indian stocks database
- Search by symbol or company name
- Sector-based browsing for easy discovery

### Interactive Charts
- Candlestick charts with OHLCV data
- Volume analysis with moving averages
- Price trend visualization
- MA50 and MA200 indicators for technical analysis

### Golden Cross & Death Cross Analysis
- Automatic detection of bullish (Golden Cross) and bearish (Death Cross) signals
- Historical cross events table with:
  - Date of crossing
  - Cross type (Golden/Death)
  - Price at crossing
  - Percentage change since the cross
  - Days since event
- Visual markers on charts for easy identification

### Performance Metrics
- Real-time price updates
- 52-week high/low tracking
- Period returns calculation
- Volatility analysis
- Volume trends

### Data Export
- Download historical data as CSV
- Customizable date ranges
- Complete OHLCV data

### Excel Watchlist Integration
- Upload and analyze Excel watchlist files
- Dynamic page creation based on file structure
- Live data integration with refresh capability

## Tech Stack

- **Frontend**: Streamlit
- **Data Source**: Yahoo Finance (yfinance)
- **Charts**: Plotly
- **Data Processing**: Pandas, NumPy
- **Language**: Python 3.11

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Step 1: Clone the Repository
```bash
git clone https://github.com/shaileshcloud2/StockScope.git
cd StockScope
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install streamlit yfinance plotly pandas openpyxl xlrd trafilatura
```

Or if you have a requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
streamlit run app.py --server.port 5000
```

The application will be available at `http://localhost:5000`

## Project Structure

```
StockScope/
├── app.py                          # Main application entry point
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── utils/
│   ├── stock_data.py               # Stock data fetching utilities
│   ├── chart_utils.py              # Chart creation functions
│   ├── stock_database.py           # Indian stocks database
│   ├── watchlist_pages.py          # Excel watchlist functionality
│   ├── live_data_fetcher.py        # Live market data integration
│   └── excel_analyzer.py           # Excel file analysis
├── attached_assets/                # Uploaded files storage
├── README.md                       # This file
└── replit.md                       # Replit-specific documentation
```

## Configuration

### Streamlit Config (.streamlit/config.toml)
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
```

## Usage Guide

### Analyzing a Stock
1. Use the sidebar search to find a stock (type symbol or company name)
2. Select from suggestions or browse by sector
3. Choose the analysis period (1 Month to 5 Years)
4. Click "Analyze Stock" button

### Golden Cross / Death Cross Analysis
1. Select a stock and choose **2 Years** or **5 Years** period
2. Scroll to the "Golden Cross & Death Cross Analysis" section
3. View the chart with cross markers and the events table

### Excel Watchlist
1. Click "View Excel Watchlists" in the sidebar
2. Navigate through different sheets
3. Filter by suggestion type, market cap, or industry
4. Use refresh button for live data updates

## Deployment

### Deploy on Replit
1. Fork this repository to Replit
2. The app will auto-configure using `.replit` and `replit.nix`
3. Click "Run" to start the application
4. Use "Publish" to make it publicly accessible

### Deploy on Streamlit Cloud
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set main file path as `app.py`
5. Deploy

### Deploy on Heroku
1. Create a `Procfile`:
   ```
   web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```
2. Create `setup.sh`:
   ```bash
   mkdir -p ~/.streamlit/
   echo "[server]
   headless = true
   port = $PORT
   enableCORS = false
   " > ~/.streamlit/config.toml
   ```
3. Deploy using Heroku CLI or GitHub integration

### Deploy with Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install streamlit yfinance plotly pandas openpyxl xlrd trafilatura

EXPOSE 5000

CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t stockscope .
docker run -p 5000:5000 stockscope
```

## Supported Exchanges

- **NSE** (National Stock Exchange) - `.NS` suffix
- **BSE** (Bombay Stock Exchange) - `.BO` suffix

## API Rate Limits

This application uses Yahoo Finance API which may have rate limits. For heavy usage, consider:
- Adding caching mechanisms
- Implementing request throttling
- Using a paid data provider

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [Yahoo Finance](https://finance.yahoo.com/) for stock data
- [Plotly](https://plotly.com/) for interactive charts

## Author

**Shailesh** - [GitHub](https://github.com/shaileshcloud2)

---

Made with love for the Indian stock market community
