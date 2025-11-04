"""
Integration tests for data collection workflow
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime
import json

from src.data_collector import PVPCDataCollector
from src.esios_client import ESIOSClient


class TestIntegrationWorkflow:
    """Integration tests simulating real workflow"""
    
    def test_full_data_collection_workflow(self):
        """Test token configuration and collector initialization"""
        # Create collector with provided token
        collector = PVPCDataCollector(
            api_token='3e5b48deb421d9a75ead2c87fb4d1e09e6aa655d264f294d698a8c7fe82d9935'
        )
        
        # Verify collector was created
        assert collector is not None
        assert collector.client is not None
        assert collector.client.token == '3e5b48deb421d9a75ead2c87fb4d1e09e6aa655d264f294d698a8c7fe82d9935'
        
        # Test data processing with sample data
        dates = pd.date_range('2024-11-01', periods=3, freq='h')
        test_df = pd.DataFrame({
            'datetime': dates,
            'value': [89.45, 87.32, 85.12],
            'indicator_id': 1001,
            'indicator_name': 'PVPC 2.0TD'
        })
        test_df.set_index('datetime', inplace=True)
        
        # Process the data
        processed_df = collector._process_data(test_df, 'pvpc_2.0TD')
        
        # Verify processing
        assert not processed_df.empty
        assert len(processed_df) == 3
        assert 'price_eur_mwh' in processed_df.columns
        assert isinstance(processed_df.index, pd.DatetimeIndex)
        assert processed_df.index.is_monotonic_increasing
        assert processed_df.index.tz is not None
    
    @patch('src.esios_client.requests.Session.get')
    def test_chunked_data_collection(self, mock_get):
        """Test data collection with chunking"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'indicator': {
                'id': 1001,
                'name': 'PVPC 2.0TD',
                'values': [
                    {
                        'datetime': f'2024-11-0{i+1}T00:00:00.000+01:00',
                        'value': 100.0 + i,
                        'datetime_utc': f'2024-10-{30+i}T23:00:00.000Z'
                    }
                    for i in range(3)
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Create client
        client = ESIOSClient(
            token='3e5b48deb421d9a75ead2c87fb4d1e09e6aa655d264f294d698a8c7fe82d9935'
        )
        
        # Test chunked collection
        df = client.get_historical_data_chunked(
            indicator_id=1001,
            start_date='2024-11-01',
            end_date='2024-11-03',
            chunk_days=1,
            delay_seconds=0  # No delay for test
        )
        
        # Should have called API multiple times (once per day)
        assert mock_get.call_count >= 1
        
        # Data should be combined
        assert not df.empty
    
    def test_data_summary_generation(self):
        """Test summary statistics generation"""
        # Create test data
        dates = pd.date_range('2024-11-01', periods=24, freq='h', tz='Europe/Madrid')
        prices = [100 + i * 2 for i in range(24)]
        df = pd.DataFrame({
            'price_eur_mwh': prices,
            'indicator_id': 1001,
            'indicator_name': 'PVPC 2.0TD'
        }, index=dates)
        
        # Create collector
        collector = PVPCDataCollector(
            api_token='3e5b48deb421d9a75ead2c87fb4d1e09e6aa655d264f294d698a8c7fe82d9935'
        )
        
        # Get summary
        summary = collector.get_data_summary(df)
        
        # Verify summary
        assert summary['total_records'] == 24
        assert summary['mean_price'] == sum(prices) / len(prices)
        assert summary['min_price'] == min(prices)
        assert summary['max_price'] == max(prices)
        assert 'start_date' in summary
        assert 'end_date' in summary
    
    def test_token_validation(self):
        """Test that provided token is used correctly"""
        token = '3e5b48deb421d9a75ead2c87fb4d1e09e6aa655d264f294d698a8c7fe82d9935'
        
        # Create client with token
        client = ESIOSClient(token=token)
        
        # Verify token is set
        assert client.token == token
        
        # Verify token is in headers
        assert 'x-api-key' in client.session.headers
        assert client.session.headers['x-api-key'] == token
    
    def test_error_handling_in_workflow(self):
        """Test error handling throughout the workflow"""
        # Test with empty token should raise ValueError
        with pytest.raises(ValueError, match="No API token provided"):
            client = ESIOSClient(token='')
