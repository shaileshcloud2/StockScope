import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

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
    
    # Add moving averages
    if len(data) >= 20:
        ma20 = data['Close'].rolling(window=20).mean()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma20,
                mode='lines',
                name='MA20',
                line=dict(color='orange', width=1, dash='dash'),
                opacity=0.8
            ),
            row=1, col=1
        )
    
    if len(data) >= 50:
        ma50 = data['Close'].rolling(window=50).mean()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma50,
                mode='lines',
                name='MA50',
                line=dict(color='blue', width=1, dash='dot'),
                opacity=0.8
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
