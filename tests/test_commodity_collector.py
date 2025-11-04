"""
Tests for commodity data collector
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import os

from src.commodity_collector import CommodityDataCollector


class TestCommodityDataCollector:
    """Test suite for CommodityDataCollector"""
    
    @patch('src.commodity_collector.DatabaseManager')
    @patch('src.commodity_collector.CapitalClient')
    def test_collector_initialization(self, mock_client, mock_db):
        """Test collector can be initialized"""
        collector = CommodityDataCollector()
        
        assert collector.client is not None
        assert collector.db is not None
        mock_db.return_value.create_tables.assert_called_once()
    
    @patch('src.commodity_collector.DatabaseManager')
    @patch('src.commodity_collector.CapitalClient')
    def test_validate_date_range(self, mock_client, mock_db):
        """Test date range validation"""
        collector = CommodityDataCollector()
        
        # Valid date range
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        collector._validate_date_range(start, end)  # Should not raise
        
        # Invalid date range (start after end)
        with pytest.raises(ValueError):
            collector._validate_date_range(end, start)
    
    @patch('src.commodity_collector.DatabaseManager')
    @patch('src.commodity_collector.CapitalClient')
    def test_validate_and_clean_data(self, mock_client, mock_db):
        """Test data validation and cleaning"""
        collector = CommodityDataCollector()
        
        # Create test dataframe with some issues
        dates = pd.date_range('2024-01-01', periods=10, freq='H')
        df = pd.DataFrame({
            'bid': [75.5, 75.6, 0, 75.8, 75.9, 76.0, 76.1, -1, 76.3, 76.4],
            'ask': [75.6, 75.7, 0.1, 75.9, 76.0, 76.1, 76.2, -0.9, 76.4, 76.5],
            'mid_price': [75.55, 75.65, 0.05, 75.85, 75.95, 76.05, 76.15, -0.95, 76.35, 76.45],
        }, index=dates)
        
        # Add duplicate
        df = pd.concat([df, df.iloc[[0]]])
        
        cleaned = collector._validate_and_clean_data(df, 'TEST_EPIC')
        
        # Should remove duplicates and invalid prices
        assert len(cleaned) < len(df)
        assert (cleaned['mid_price'] > 0).all()
    
    @patch('src.commodity_collector.DatabaseManager')
    @patch('src.commodity_collector.CapitalClient')
    def test_collect_historical_data(self, mock_client, mock_db):
        """Test collecting historical data"""
        # Setup mocks
        mock_client_instance = mock_client.return_value
        mock_db_instance = mock_db.return_value
        
        # Mock price data
        dates = pd.date_range('2024-01-01', periods=5, freq='H')
        mock_df = pd.DataFrame({
            'bid': [75.5, 75.6, 75.7, 75.8, 75.9],
            'ask': [75.6, 75.7, 75.8, 75.9, 76.0],
            'mid_price': [75.55, 75.65, 75.75, 75.85, 75.95],
            'epic': ['CRUDE_OIL'] * 5,
            'instrument_type': ['COMMODITIES'] * 5
        }, index=dates)
        
        mock_client_instance.get_historical_prices_chunked.return_value = mock_df
        mock_client_instance.get_market_details.return_value = {
            'instrument': {
                'symbol': 'Crude Oil',
                'name': 'Crude Oil',
                'type': 'COMMODITIES',
                'currency': 'USD',
                'lotSize': 1.0
            }
        }
        
        collector = CommodityDataCollector()
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        df = collector.collect_historical_data(
            epic='CRUDE_OIL',
            start_date=start_date,
            end_date=end_date,
            resolution='HOUR',
            save_to_file=False,
            save_to_db=False
        )
        
        assert not df.empty
        assert len(df) == 5
        mock_client_instance.get_historical_prices_chunked.assert_called_once()
    
    @patch('src.commodity_collector.DatabaseManager')
    @patch('src.commodity_collector.CapitalClient')
    def test_get_data_summary(self, mock_client, mock_db):
        """Test getting data summary"""
        collector = CommodityDataCollector()
        
        dates = pd.date_range('2024-01-01', periods=10, freq='H')
        df = pd.DataFrame({
            'mid_price': [75.0, 76.0, 77.0, 78.0, 79.0, 80.0, 81.0, 82.0, 83.0, 84.0],
        }, index=dates)
        
        summary = collector.get_data_summary(df)
        
        assert summary['total_records'] == 10
        assert 'mean_price' in summary
        assert 'min_price' in summary
        assert 'max_price' in summary
        assert summary['min_price'] == 75.0
        assert summary['max_price'] == 84.0
    
    @patch('src.commodity_collector.DatabaseManager')
    @patch('src.commodity_collector.CapitalClient')
    def test_update_daily(self, mock_client, mock_db):
        """Test daily update functionality"""
        mock_client_instance = mock_client.return_value
        mock_db_instance = mock_db.return_value
        
        # Mock that we have data up to yesterday
        last_date = datetime.now() - timedelta(days=1)
        mock_db_instance.get_latest_date.return_value = last_date
        
        # Mock new data
        dates = pd.date_range(last_date + timedelta(hours=1), periods=5, freq='H')
        mock_df = pd.DataFrame({
            'bid': [75.5, 75.6, 75.7, 75.8, 75.9],
            'ask': [75.6, 75.7, 75.8, 75.9, 76.0],
            'mid_price': [75.55, 75.65, 75.75, 75.85, 75.95],
            'epic': ['CRUDE_OIL'] * 5,
            'instrument_type': ['COMMODITIES'] * 5
        }, index=dates)
        
        mock_client_instance.get_historical_prices_chunked.return_value = mock_df
        mock_client_instance.get_market_details.return_value = {
            'instrument': {
                'symbol': 'Crude Oil',
                'name': 'Crude Oil',
                'type': 'COMMODITIES'
            }
        }
        
        collector = CommodityDataCollector()
        
        # Mock COMMODITY_EPICS to have just one for testing
        with patch('src.commodity_collector.COMMODITY_EPICS', {'crude_oil_rt': 'CRUDE_OIL'}):
            results = collector.update_daily(resolution='HOUR')
        
        assert 'crude_oil_rt' in results
        # get_latest_date should have been called
        mock_db_instance.get_latest_date.assert_called()
