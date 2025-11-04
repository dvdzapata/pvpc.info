"""
Tests for database models and operations
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import os

from src.database import DatabaseManager, CommodityPrice, CommodityMetadata


class TestDatabaseManager:
    """Test suite for DatabaseManager"""
    
    def test_initialization(self):
        """Test database manager initialization"""
        # Use in-memory SQLite for testing
        db = DatabaseManager(database_url='sqlite:///:memory:')
        assert db.engine is not None
        assert db.SessionLocal is not None
    
    def test_create_tables(self):
        """Test table creation"""
        db = DatabaseManager(database_url='sqlite:///:memory:')
        db.create_tables()
        
        # Verify tables exist
        session = db.get_session()
        try:
            # Try to query tables - should not raise
            session.query(CommodityPrice).first()
            session.query(CommodityMetadata).first()
        finally:
            session.close()
    
    def test_insert_prices(self):
        """Test inserting price data"""
        db = DatabaseManager(database_url='sqlite:///:memory:')
        db.create_tables()
        
        # Create test dataframe
        dates = pd.date_range('2024-01-01', periods=5, freq='H')
        df = pd.DataFrame({
            'bid': [75.5, 75.6, 75.7, 75.8, 75.9],
            'ask': [75.6, 75.7, 75.8, 75.9, 76.0],
            'mid_price': [75.55, 75.65, 75.75, 75.85, 75.95],
            'lastTradedVolume': [1000, 1100, 1200, 1300, 1400],
            'instrument_type': ['COMMODITIES'] * 5
        }, index=dates)
        
        count = db.insert_prices(df, 'CRUDE_OIL', 'HOUR')
        
        assert count == 5
        
        # Verify data was inserted
        session = db.get_session()
        try:
            records = session.query(CommodityPrice).filter_by(epic='CRUDE_OIL').all()
            assert len(records) == 5
            assert records[0].mid_price == 75.55
        finally:
            session.close()
    
    def test_update_prices(self):
        """Test updating existing price data"""
        db = DatabaseManager(database_url='sqlite:///:memory:')
        db.create_tables()
        
        # Insert initial data
        dates = pd.date_range('2024-01-01', periods=3, freq='H')
        df1 = pd.DataFrame({
            'bid': [75.5, 75.6, 75.7],
            'ask': [75.6, 75.7, 75.8],
            'mid_price': [75.55, 75.65, 75.75],
            'instrument_type': ['COMMODITIES'] * 3
        }, index=dates)
        
        db.insert_prices(df1, 'CRUDE_OIL', 'HOUR')
        
        # Update with new data for same dates
        df2 = pd.DataFrame({
            'bid': [76.5, 76.6, 76.7],
            'ask': [76.6, 76.7, 76.8],
            'mid_price': [76.55, 76.65, 76.75],
            'instrument_type': ['COMMODITIES'] * 3
        }, index=dates)
        
        count = db.insert_prices(df2, 'CRUDE_OIL', 'HOUR')
        
        # Should update, not insert new
        assert count == 0
        
        # Verify data was updated
        session = db.get_session()
        try:
            records = session.query(CommodityPrice).filter_by(epic='CRUDE_OIL').all()
            assert len(records) == 3
            assert records[0].mid_price == 76.55
        finally:
            session.close()
    
    def test_update_metadata(self):
        """Test updating commodity metadata"""
        db = DatabaseManager(database_url='sqlite:///:memory:')
        db.create_tables()
        
        metadata = {
            'symbol': 'CRUDE',
            'name': 'Crude Oil',
            'instrument_type': 'COMMODITIES',
            'currency': 'USD',
            'lot_size': 1.0,
            'total_records': 100
        }
        
        db.update_metadata('CRUDE_OIL', metadata)
        
        # Verify metadata was inserted
        session = db.get_session()
        try:
            record = session.query(CommodityMetadata).filter_by(epic='CRUDE_OIL').first()
            assert record is not None
            assert record.name == 'Crude Oil'
            assert record.currency == 'USD'
        finally:
            session.close()
    
    def test_get_latest_date(self):
        """Test getting latest date for an EPIC"""
        db = DatabaseManager(database_url='sqlite:///:memory:')
        db.create_tables()
        
        # Insert data with different dates
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'bid': [75.5] * 5,
            'ask': [75.6] * 5,
            'mid_price': [75.55] * 5,
            'instrument_type': ['COMMODITIES'] * 5
        }, index=dates)
        
        db.insert_prices(df, 'CRUDE_OIL', 'DAY')
        
        latest = db.get_latest_date('CRUDE_OIL')
        
        assert latest is not None
        assert latest.date() == datetime(2024, 1, 5).date()
    
    def test_get_data_count(self):
        """Test getting count of records"""
        db = DatabaseManager(database_url='sqlite:///:memory:')
        db.create_tables()
        
        # Insert data
        dates = pd.date_range('2024-01-01', periods=10, freq='H')
        df = pd.DataFrame({
            'bid': [75.5] * 10,
            'ask': [75.6] * 10,
            'mid_price': [75.55] * 10,
            'instrument_type': ['COMMODITIES'] * 10
        }, index=dates)
        
        db.insert_prices(df, 'CRUDE_OIL', 'HOUR')
        
        count = db.get_data_count('CRUDE_OIL')
        assert count == 10
    
    def test_get_latest_date_no_data(self):
        """Test getting latest date when no data exists"""
        db = DatabaseManager(database_url='sqlite:///:memory:')
        db.create_tables()
        
        latest = db.get_latest_date('NONEXISTENT')
        assert latest is None
    
    def test_insert_empty_dataframe(self):
        """Test inserting empty dataframe"""
        db = DatabaseManager(database_url='sqlite:///:memory:')
        db.create_tables()
        
        df = pd.DataFrame()
        count = db.insert_prices(df, 'CRUDE_OIL', 'HOUR')
        
        assert count == 0
