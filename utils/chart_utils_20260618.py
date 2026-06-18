import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def detect_golden_death_cross(data):
    """
    Detect Golden Cross and Death Cross patterns in stock data.
    
    Golden Cross: MA50 crosses above MA200 (bullish signal)
    Death Cross: MA50 crosses below MA200 (bearish signal)
    
    Args:
        data (pd.DataFrame): Stock data with Close prices
        
    Returns:
        pd.DataFrame: DataFrame with cross events including date, type, and percentage change
    """
    if len(data) < 200:
        return pd.DataFrame(columns=['Date', 'Cross Type', 'Close Price', 'Current Price', '% Change', 'Days Since'])
    
    df = data.copy()
    
    # Calculate moving averages
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    df['MA_200'] = df['Close'].rolling(window=200).mean()
    
    # Detect crossovers
    df['Golden_Cross'] = (df['MA_50'] > df['MA_200']) & (df['MA_50'].shift(1) <= df['MA_200'].shift(1))
    df['Death_Cross'] = (df['MA_50'] < df['MA_200']) & (df['MA_50'].shift(1) >= df['MA_200'].shift(1))
    
    # Get current price for percentage calculation
    current_price = df['Close'].iloc[-1]
    current_date = df.index[-1]
    
    # Collect cross events
    cross_events = []
    
    # Golden Cross events
    golden_crosses = df[df['Golden_Cross'] == True]
    for idx, row in golden_crosses.iterrows():
        close_price = row['Close']
        pct_change = ((current_price - close_price) / close_price) * 100
        days_since = (current_date - idx).days
        cross_events.append({
            'Date': idx.strftime('%Y-%m-%d'),
            'Cross Type': 'Golden Cross',
            'Close Price': f"₹{close_price:,.2f}",
            'Current Price': f"₹{current_price:,.2f}",
            '% Change': f"{pct_change:+.2f}%",
            'Days Since': days_since,
            'pct_value': pct_change  # For sorting
        })
    
    # Death Cross events
    death_crosses = df[df['Death_Cross'] == True]
    for idx, row in death_crosses.iterrows():
        close_price = row['Close']
        pct_change = ((current_price - close_price) / close_price) * 100
        days_since = (current_date - idx).days
        cross_events.append({
            'Date': idx.strftime('%Y-%m-%d'),
            'Cross Type': 'Death Cross',
            'Close Price': f"₹{close_price:,.2f}",
            'Current Price': f"₹{current_price:,.2f}",
            '% Change': f"{pct_change:+.2f}%",
            'Days Since': days_since,
            'pct_value': pct_change  # For sorting
        })
    
    # Create DataFrame and sort by date
    if cross_events:
        result_df = pd.DataFrame(cross_events)
        result_df = result_df.sort_values('Date', ascending=False)
        # Drop the sorting column
        result_df = result_df.drop(columns=['pct_value'])
        return result_df
    else:
        return pd.DataFrame(columns=['Date', 'Cross Type', 'Close Price', 'Current Price', '% Change', 'Days Since'])


def create_cross_analysis_chart(data, symbol):
    """
    Create a chart highlighting Golden Cross and Death Cross events.
    
    Args:
        data (pd.DataFrame): Stock data with OHLCV columns
        symbol (str): Stock symbol
        
    Returns:
        plotly.graph_objects.Figure: Interactive chart with cross markers
    """
    if len(data) < 200:
        return None
    
    df = data.copy()
    
    # Calculate moving averages
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    df['MA_200'] = df['Close'].rolling(window=200).mean()
    
    # Detect crossovers
    df['Golden_Cross'] = (df['MA_50'] > df['MA_200']) & (df['MA_50'].shift(1) <= df['MA_200'].shift(1))
    df['Death_Cross'] = (df['MA_50'] < df['MA_200']) & (df['MA_50'].shift(1) >= df['MA_200'].shift(1))
    
    fig = go.Figure()
    
    # Add close price line
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#00ff88', width=2),
            opacity=0.8
        )
    )
    
    # Add MA50 line
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['MA_50'],
            mode='lines',
            name='MA 50',
            line=dict(color='#FFD700', width=2),
            opacity=0.9
        )
    )
    
    # Add MA200 line
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['MA_200'],
            mode='lines',
            name='MA 200',
            line=dict(color='#FF6B6B', width=2),
            opacity=0.9
        )
    )
    
    # Add Golden Cross markers
    golden_df = df[df['Golden_Cross'] == True]
    if not golden_df.empty:
        fig.add_trace(
            go.Scatter(
                x=golden_df.index,
                y=golden_df['Close'],
                mode='markers',
                name='Golden Cross',
                marker=dict(
                    symbol='triangle-up',
                    size=15,
                    color='#00FF00',
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>Golden Cross</b><br>' +
                             'Date: %{x}<br>' +
                             'Price: ₹%{y:,.2f}<br>' +
                             '<extra></extra>'
            )
        )
    
    # Add Death Cross markers
    death_df = df[df['Death_Cross'] == True]
    if not death_df.empty:
        fig.add_trace(
            go.Scatter(
                x=death_df.index,
                y=death_df['Close'],
                mode='markers',
                name='Death Cross',
                marker=dict(
                    symbol='triangle-down',
                    size=15,
                    color='#FF0000',
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>Death Cross</b><br>' +
                             'Date: %{x}<br>' +
                             'Price: ₹%{y:,.2f}<br>' +
                             '<extra></extra>'
            )
        )
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} - Golden Cross & Death Cross Analysis',
        xaxis_title='Date',
        yaxis_title='Price (₹)',
        template='plotly_dark',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        hovermode='x unified',
        height=500
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    return fig

def create_price_chart(data, symbol, chart_type="candlestick"):
    """
    Create an interactive price chart for stock data.
    
    Args:
        data (pd.DataFrame): Stock data with OHLCV columns
        symbol (str): Stock symbol for title
        chart_type (str): Type of chart - 'candlestick', 'line', or 'ohlc'
    
    Returns:
        plotly.graph_objects.Figure: Interactive price chart
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[f'{symbol} - Stock Price', 'Volume'],
        row_width=[0.7, 0.3]
    )
    
    # Price chart
    if chart_type == "candlestick":
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price',
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444',
                increasing_fillcolor='#00ff88',
                decreasing_fillcolor='#ff4444'
            ),
            row=1, col=1
        )
    elif chart_type == "line":
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='#00ff88', width=2)
            ),
            row=1, col=1
        )
    else:  # OHLC
        fig.add_trace(
            go.Ohlc(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='OHLC',
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444'
            ),
            row=1, col=1
        )
    
    # Volume bars
    colors = ['#00ff88' if close >= open else '#ff4444' 
             for close, open in zip(data['Close'], data['Open'])]
    
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # Add moving averages (MA50 and MA200 for Golden/Death Cross analysis)
    if len(data) >= 50:
        ma50 = data['Close'].rolling(window=50).mean()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma50,
                mode='lines',
                name='MA50',
                line=dict(color='#FFD700', width=2),
                opacity=0.9
            ),
            row=1, col=1
        )
    
    if len(data) >= 200:
        ma200 = data['Close'].rolling(window=200).mean()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma200,
                mode='lines',
                name='MA200',
                line=dict(color='#FF6B6B', width=2),
                opacity=0.9
            ),
            row=1, col=1
        )
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} - Stock Analysis',
        yaxis_title='Price (₹)',
        yaxis2_title='Volume',
        xaxis2_title='Date',
        template='plotly_dark',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        hovermode='x unified',
        height=600
    )
    
    # Remove rangeslider from candlestick
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    # Update x-axis
    fig.update_xaxes(
        title_text="Date",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    # Update y-axes
    fig.update_yaxes(
        title_text="Price (₹)",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        row=1, col=1
    )
    
    fig.update_yaxes(
        title_text="Volume",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        row=2, col=1
    )
    
    return fig

def create_volume_chart(data, symbol):
    """
    Create a dedicated volume chart with volume analysis.
    
    Args:
        data (pd.DataFrame): Stock data with Volume column
        symbol (str): Stock symbol for title
    
    Returns:
        plotly.graph_objects.Figure: Interactive volume chart
    """
    fig = go.Figure()
    
    # Volume bars with color based on price movement
    colors = ['#00ff88' if close >= open else '#ff4444' 
             for close, open in zip(data['Close'], data['Open'])]
    
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.8,
            hovertemplate='<b>Date:</b> %{x}<br>' +
                         '<b>Volume:</b> %{y:,.0f}<br>' +
                         '<extra></extra>'
        )
    )
    
    # Add volume moving average
    if len(data) >= 20:
        vol_ma = data['Volume'].rolling(window=20).mean()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=vol_ma,
                mode='lines',
                name='Volume MA(20)',
                line=dict(color='yellow', width=2),
                opacity=0.8,
                hovertemplate='<b>Date:</b> %{x}<br>' +
                             '<b>Volume MA20:</b> %{y:,.0f}<br>' +
                             '<extra></extra>'
            )
        )
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} - Volume Analysis',
        xaxis_title='Date',
        yaxis_title='Volume',
        template='plotly_dark',
        showlegend=True,
        hovermode='x unified',
        height=400
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    return fig

def create_returns_chart(data, symbol, period="1y"):
    """
    Create a returns analysis chart.
    
    Args:
        data (pd.DataFrame): Stock data
        symbol (str): Stock symbol
        period (str): Period for analysis
    
    Returns:
        plotly.graph_objects.Figure: Returns chart
    """
    # Calculate daily returns
    returns = data['Close'].pct_change().dropna()
    
    # Calculate cumulative returns
    cumulative_returns = (1 + returns).cumprod() - 1
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[f'{symbol} - Cumulative Returns', 'Daily Returns Distribution'],
        vertical_spacing=0.1
    )
    
    # Cumulative returns line chart
    fig.add_trace(
        go.Scatter(
            x=cumulative_returns.index,
            y=cumulative_returns * 100,
            mode='lines',
            name='Cumulative Returns (%)',
            line=dict(color='#00ff88', width=2),
            fill='tonexty',
            fillcolor='rgba(0,255,136,0.1)'
        ),
        row=1, col=1
    )
    
    # Daily returns histogram
    fig.add_trace(
        go.Histogram(
            x=returns * 100,
            name='Daily Returns (%)',
            nbinsx=50,
            marker_color='#ff6b6b',
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=f'{symbol} - Returns Analysis',
        template='plotly_dark',
        showlegend=False,
        height=600
    )
    
    # Update axes
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative Returns (%)", row=1, col=1)
    fig.update_xaxes(title_text="Daily Returns (%)", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    
    return fig

def create_comparison_chart(stocks_data, symbols, period="6mo"):
    """
    Create a comparison chart for multiple stocks.
    
    Args:
        stocks_data (dict): Dictionary of stock data {symbol: dataframe}
        symbols (list): List of stock symbols
        period (str): Period for comparison
    
    Returns:
        plotly.graph_objects.Figure: Comparison chart
    """
    fig = go.Figure()
    
    colors = ['#00ff88', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
    
    for i, symbol in enumerate(symbols):
        if symbol in stocks_data and stocks_data[symbol] is not None:
            data = stocks_data[symbol]
            # Normalize to percentage change from first value
            normalized = ((data['Close'] / data['Close'].iloc[0]) - 1) * 100
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=normalized,
                    mode='lines',
                    name=symbol,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f'<b>{symbol}</b><br>' +
                                 '<b>Date:</b> %{x}<br>' +
                                 '<b>Return:</b> %{y:.2f}%<br>' +
                                 '<extra></extra>'
                )
            )
    
    # Add horizontal line at 0%
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Update layout
    fig.update_layout(
        title='Stock Performance Comparison',
        xaxis_title='Date',
        yaxis_title='Returns (%)',
        template='plotly_dark',
        hovermode='x unified',
        height=500,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    return fig
