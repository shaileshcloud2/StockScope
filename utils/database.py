"""
Database module for StockScope application
Handles PostgreSQL database operations for stock data, user preferences, and analysis caching
"""

import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import streamlit as st
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection setup
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DatabaseManager:
    """Main database manager for StockScope application"""
    
    def __init__(self):
        self.engine = engine
        self.metadata = MetaData()
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            # Historical stock data table
            stock_data_table = Table('stock_data', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('symbol', String(20), nullable=False),
                Column('date', DateTime, nullable=False),
                Column('open_price', Float, nullable=False),
                Column('high_price', Float, nullable=False),
                Column('low_price', Float, nullable=False),
                Column('close_price', Float, nullable=False),
                Column('adj_close_price', Float),
                Column('volume', Integer, nullable=False),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            )
            
            # User watchlists table
            watchlists_table = Table('watchlists', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('user_id', String(50), nullable=False),
                Column('watchlist_name', String(100), nullable=False),
                Column('symbols', JSON, nullable=False),  # Store as JSON array
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            )
            
            # Stock analysis cache table
            analysis_cache_table = Table('analysis_cache', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('symbol', String(20), nullable=False),
                Column('period', String(10), nullable=False),
                Column('analysis_data', JSON, nullable=False),
                Column('cached_at', DateTime, default=datetime.utcnow),
                Column('expires_at', DateTime, nullable=False)
            )
            
            # Stock alerts table
            alerts_table = Table('stock_alerts', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('user_id', String(50), nullable=False),
                Column('symbol', String(20), nullable=False),
                Column('alert_type', String(20), nullable=False),  # 'price_above', 'price_below', 'volume_spike'
                Column('target_value', Float, nullable=False),
                Column('is_active', Boolean, default=True),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('triggered_at', DateTime)
            )
            
            # User preferences table
            user_preferences_table = Table('user_preferences', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('user_id', String(50), nullable=False, unique=True),
                Column('default_period', String(10), default='1y'),
                Column('preferred_charts', JSON, default=['candlestick', 'volume']),
                Column('dashboard_layout', JSON),
                Column('notification_settings', JSON),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            )
            
            # Market indices data table
            market_indices_table = Table('market_indices', self.metadata,
                Column('id', Integer, primary_key=True),
                Column('index_name', String(20), nullable=False),  # NIFTY50, SENSEX, etc.
                Column('date', DateTime, nullable=False),
                Column('open_value', Float, nullable=False),
                Column('high_value', Float, nullable=False),
                Column('low_value', Float, nullable=False),
                Column('close_value', Float, nullable=False),
                Column('volume', Integer),
                Column('created_at', DateTime, default=datetime.utcnow)
            )
            
            # Create all tables
            self.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    def store_stock_data(self, symbol: str, data: pd.DataFrame) -> bool:
        """Store stock data in the database"""
        try:
            # Prepare data for insertion
            data_to_insert = []
            
            for index, row in data.iterrows():
                data_to_insert.append({
                    'symbol': symbol,
                    'date': index,
                    'open_price': row['Open'],
                    'high_price': row['High'],
                    'low_price': row['Low'],
                    'close_price': row['Close'],
                    'adj_close_price': row.get('Adj Close', row['Close']),
                    'volume': int(row['Volume'])
                })
            
            # Insert data using pandas to_sql for efficiency
            df_insert = pd.DataFrame(data_to_insert)
            df_insert.to_sql('stock_data', self.engine, if_exists='append', index=False, method='multi')
            
            logger.info(f"Successfully stored {len(data_to_insert)} records for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing stock data for {symbol}: {str(e)}")
            return False
    
    def get_stock_data(self, symbol: str, period: str = '1y') -> pd.DataFrame:
        """Retrieve stock data from database"""
        try:
            # Calculate date range based on period
            end_date = datetime.now()
            period_days = {
                '1mo': 30, '3mo': 90, '6mo': 180, 
                '1y': 365, '2y': 730, '5y': 1825
            }
            start_date = end_date - timedelta(days=period_days.get(period, 365))
            
            query = text("""
                SELECT date, open_price as "Open", high_price as "High", 
                       low_price as "Low", close_price as "Close", 
                       adj_close_price as "Adj Close", volume as "Volume"
                FROM stock_data 
                WHERE symbol = :symbol 
                AND date >= :start_date 
                AND date <= :end_date
                ORDER BY date ASC
            """)
            
            df = pd.read_sql(query, self.engine, params={
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date
            })
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving stock data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def create_watchlist(self, user_id: str, watchlist_name: str, symbols: list) -> bool:
        """Create a new watchlist for a user"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    INSERT INTO watchlists (user_id, watchlist_name, symbols)
                    VALUES (:user_id, :watchlist_name, :symbols)
                """)
                
                conn.execute(query, {
                    'user_id': user_id,
                    'watchlist_name': watchlist_name,
                    'symbols': json.dumps(symbols)
                })
                conn.commit()
            
            logger.info(f"Created watchlist '{watchlist_name}' for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating watchlist: {str(e)}")
            return False
    
    def get_user_watchlists(self, user_id: str) -> list:
        """Get all watchlists for a user"""
        try:
            query = text("""
                SELECT id, watchlist_name, symbols, created_at
                FROM watchlists 
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'user_id': user_id})
                watchlists = []
                
                for row in result:
                    watchlists.append({
                        'id': row[0],
                        'name': row[1],
                        'symbols': json.loads(row[2]),
                        'created_at': row[3]
                    })
                
                return watchlists
                
        except Exception as e:
            logger.error(f"Error retrieving watchlists for user {user_id}: {str(e)}")
            return []
    
    def cache_analysis(self, symbol: str, period: str, analysis_data: dict, cache_hours: int = 1) -> bool:
        """Cache analysis results for faster retrieval"""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=cache_hours)
            
            with self.engine.connect() as conn:
                # First, delete any existing cache for this symbol/period
                delete_query = text("""
                    DELETE FROM analysis_cache 
                    WHERE symbol = :symbol AND period = :period
                """)
                conn.execute(delete_query, {'symbol': symbol, 'period': period})
                
                # Insert new cache entry
                insert_query = text("""
                    INSERT INTO analysis_cache (symbol, period, analysis_data, expires_at)
                    VALUES (:symbol, :period, :analysis_data, :expires_at)
                """)
                
                conn.execute(insert_query, {
                    'symbol': symbol,
                    'period': period,
                    'analysis_data': json.dumps(analysis_data),
                    'expires_at': expires_at
                })
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching analysis: {str(e)}")
            return False
    
    def get_cached_analysis(self, symbol: str, period: str) -> dict:
        """Retrieve cached analysis if still valid"""
        try:
            query = text("""
                SELECT analysis_data
                FROM analysis_cache 
                WHERE symbol = :symbol 
                AND period = :period 
                AND expires_at > :current_time
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {
                    'symbol': symbol,
                    'period': period,
                    'current_time': datetime.utcnow()
                })
                
                row = result.fetchone()
                if row:
                    return json.loads(row[0])
                
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving cached analysis: {str(e)}")
            return {}
    
    def create_price_alert(self, user_id: str, symbol: str, alert_type: str, target_value: float) -> bool:
        """Create a price alert for a user"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    INSERT INTO stock_alerts (user_id, symbol, alert_type, target_value)
                    VALUES (:user_id, :symbol, :alert_type, :target_value)
                """)
                
                conn.execute(query, {
                    'user_id': user_id,
                    'symbol': symbol,
                    'alert_type': alert_type,
                    'target_value': target_value
                })
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating price alert: {str(e)}")
            return False
    
    def get_user_alerts(self, user_id: str) -> list:
        """Get all active alerts for a user"""
        try:
            query = text("""
                SELECT id, symbol, alert_type, target_value, created_at
                FROM stock_alerts 
                WHERE user_id = :user_id AND is_active = true
                ORDER BY created_at DESC
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'user_id': user_id})
                alerts = []
                
                for row in result:
                    alerts.append({
                        'id': row[0],
                        'symbol': row[1],
                        'alert_type': row[2],
                        'target_value': row[3],
                        'created_at': row[4]
                    })
                
                return alerts
                
        except Exception as e:
            logger.error(f"Error retrieving alerts for user {user_id}: {str(e)}")
            return []
    
    def save_user_preferences(self, user_id: str, preferences: dict) -> bool:
        """Save user preferences to database"""
        try:
            with self.engine.connect() as conn:
                # Check if preferences exist
                check_query = text("""
                    SELECT id FROM user_preferences WHERE user_id = :user_id
                """)
                result = conn.execute(check_query, {'user_id': user_id})
                exists = result.fetchone()
                
                if exists:
                    # Update existing preferences
                    update_query = text("""
                        UPDATE user_preferences 
                        SET default_period = :default_period,
                            preferred_charts = :preferred_charts,
                            dashboard_layout = :dashboard_layout,
                            notification_settings = :notification_settings,
                            updated_at = :updated_at
                        WHERE user_id = :user_id
                    """)
                    conn.execute(update_query, {
                        'user_id': user_id,
                        'default_period': preferences.get('default_period', '1y'),
                        'preferred_charts': json.dumps(preferences.get('preferred_charts', ['candlestick', 'volume'])),
                        'dashboard_layout': json.dumps(preferences.get('dashboard_layout', {})),
                        'notification_settings': json.dumps(preferences.get('notification_settings', {})),
                        'updated_at': datetime.utcnow()
                    })
                else:
                    # Insert new preferences
                    insert_query = text("""
                        INSERT INTO user_preferences 
                        (user_id, default_period, preferred_charts, dashboard_layout, notification_settings)
                        VALUES (:user_id, :default_period, :preferred_charts, :dashboard_layout, :notification_settings)
                    """)
                    conn.execute(insert_query, {
                        'user_id': user_id,
                        'default_period': preferences.get('default_period', '1y'),
                        'preferred_charts': json.dumps(preferences.get('preferred_charts', ['candlestick', 'volume'])),
                        'dashboard_layout': json.dumps(preferences.get('dashboard_layout', {})),
                        'notification_settings': json.dumps(preferences.get('notification_settings', {}))
                    })
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving user preferences: {str(e)}")
            return False
    
    def get_user_preferences(self, user_id: str) -> dict:
        """Get user preferences from database"""
        try:
            query = text("""
                SELECT default_period, preferred_charts, dashboard_layout, notification_settings
                FROM user_preferences 
                WHERE user_id = :user_id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'user_id': user_id})
                row = result.fetchone()
                
                if row:
                    return {
                        'default_period': row[0],
                        'preferred_charts': json.loads(row[1]),
                        'dashboard_layout': json.loads(row[2]),
                        'notification_settings': json.loads(row[3])
                    }
                
                # Return default preferences if user not found
                return {
                    'default_period': '1y',
                    'preferred_charts': ['candlestick', 'volume'],
                    'dashboard_layout': {},
                    'notification_settings': {}
                }
                
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {str(e)}")
            return {
                'default_period': '1y',
                'preferred_charts': ['candlestick', 'volume'],
                'dashboard_layout': {},
                'notification_settings': {}
            }
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Clean up old cached data and analysis"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with self.engine.connect() as conn:
                # Clean old cache entries
                cache_query = text("""
                    DELETE FROM analysis_cache 
                    WHERE cached_at < :cutoff_date
                """)
                conn.execute(cache_query, {'cutoff_date': cutoff_date})
                
                # Clean old stock data (keep only recent data to prevent database bloat)
                # This is optional and depends on your data retention policy
                
                conn.commit()
                logger.info(f"Cleaned up data older than {days_to_keep} days")
                return True
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return False
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            stats = {}
            
            with self.engine.connect() as conn:
                # Count records in each table
                tables = ['stock_data', 'watchlists', 'analysis_cache', 'stock_alerts', 'user_preferences']
                
                for table in tables:
                    count_query = text(f"SELECT COUNT(*) FROM {table}")
                    result = conn.execute(count_query)
                    stats[f'{table}_count'] = result.fetchone()[0]
                
                # Get unique symbols count
                symbols_query = text("SELECT COUNT(DISTINCT symbol) FROM stock_data")
                result = conn.execute(symbols_query)
                stats['unique_symbols'] = result.fetchone()[0]
                
                # Get date range of stored data
                date_range_query = text("""
                    SELECT MIN(date) as min_date, MAX(date) as max_date 
                    FROM stock_data
                """)
                result = conn.execute(date_range_query)
                row = result.fetchone()
                if row[0]:
                    stats['data_date_range'] = {
                        'min_date': row[0].strftime('%Y-%m-%d'),
                        'max_date': row[1].strftime('%Y-%m-%d')
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}

# Global database manager instance
@st.cache_resource
def get_database_manager():
    """Get database manager instance (cached)"""
    return DatabaseManager()

# Utility functions for Streamlit integration
def init_user_session():
    """Initialize user session with database support"""
    if 'user_id' not in st.session_state:
        # Generate a simple user ID based on session
        import hashlib
        session_id = st.session_info.session_id if hasattr(st, 'session_info') else 'default_user'
        st.session_state.user_id = hashlib.md5(session_id.encode()).hexdigest()[:16]
    
    return st.session_state.user_id

def store_stock_data_async(symbol: str, data: pd.DataFrame):
    """Asynchronously store stock data in database"""
    try:
        db_manager = get_database_manager()
        success = db_manager.store_stock_data(symbol, data)
        
        if success:
            logger.info(f"Successfully cached {symbol} data in database")
        else:
            logger.warning(f"Failed to cache {symbol} data in database")
            
    except Exception as e:
        logger.error(f"Error in async stock data storage: {str(e)}")