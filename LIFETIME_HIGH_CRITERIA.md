# Near Lifetime High + Cup & Handle Criteria Report

## 1. Overview
This document outlines the detailed technical and financial logic used to identify high-potential breakout stocks in the StockScope application.

## 2. Data Sourcing
- **Data Source**: Yahoo Finance API (via `yfinance`).
- **Timeframe**: Maximum historical data (`period="max"`) to ensure true "Lifetime High" identification.
- **Interval**: Monthly (`1mo`) charts are prioritized for long-term structural analysis. Weekly (`1wk`) charts are used as a fallback for newer listings.

## 3. Lifetime High (ATH) Logic
- **Definition**: The maximum price reached in the entire historical dataset provided by the exchange.
- **Scanning Range**: The system identifies stocks where the current price is between **2% below** to **5% above** the previous Lifetime High.
  - *Below range*: Identifies stocks consolidating under resistance (potential breakout).
  - *Above range*: Identifies stocks in the early stages of a "Blue Sky" breakout.

## 4. Cup & Handle Pattern Detection Logic
The pattern is detected using a multi-step heuristic approach on the monthly/weekly price series:

### A. Cup Structure
1. **Prior High**: The system identifies a significant local high (the "Lip" of the cup) in the previous 5-20 years of data.
2. **Cup Depth**: A significant decline (minimum 15-20%) followed by a "U-shaped" recovery back towards the prior high.
3. **Recovery**: The price must recover to at least 85% of the prior high's value to confirm a completed cup.

### B. Handle Structure
1. **Consolidation**: After reaching the "Lip," the price must undergo a smaller consolidation or slight pullback.
2. **Handle Depth**: The pullback should generally not exceed 10-15% of the cup lip's price.
3. **Handle Duration**: Measured over the last 4-8 candles (weeks/months depending on the chart).

### C. Breakout Identification
- **Range Verification**: The "Handle" must be forming within the 2% below to 5% above ATH range.
- **Momentum Check**: RSI is calculated to ensure the stock is not excessively overextended (RSI > 80) but maintains bullish momentum (RSI > 50).

## 5. Output Metrics
- **RSI**: Relative Strength Index to gauge momentum.
- **PE Ratio**: Trailing Price-to-Earnings for valuation context.
- **Volume**: Recent trading activity to confirm participation.
- **Suggestion**: 
  - *Breakout Momentum BUY*: For stocks already trading 0-5% above the old high.
  - *BUY on Breakout*: For stocks consolidating just below the lip.

## 6. Visualization
The system renders a candlestick chart showing the last 120 data points (approx. 10 years of monthly data) to provide visual confirmation of the multi-year base.
