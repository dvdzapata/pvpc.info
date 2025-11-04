"""
Tests for Capital.com API client
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

from src.capital_client import CapitalClient


class TestCapitalClient:
    """Test suite for CapitalClient"""
    
    def test_client_initialization(self):
        """Test client can be initialized"""
        client = CapitalClient()
        assert client.base_url == "https://api-capital.backend-capital.com/api/v1"
        assert client.session is not None
    
    @patch('src.capital_client.requests.Session.get')
    def test_get_markets(self, mock_get):
        """Test getting market data"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'markets': [
                {
                    'epic': 'CRUDE_OIL',
                    'symbol': 'Crude Oil',
                    'bid': 75.5,
                    'offer': 75.6,
                    'instrumentType': 'COMMODITIES'
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = CapitalClient()
        markets = client.get_markets()
        
        assert len(markets) == 1
        assert markets[0]['epic'] == 'CRUDE_OIL'
    
    @patch('src.capital_client.requests.Session.get')
    def test_get_market_details(self, mock_get):
        """Test getting market details"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'instrument': {
                'epic': 'CRUDE_OIL',
                'symbol': 'Crude Oil',
                'name': 'Crude Oil',
                'type': 'COMMODITIES',
                'currency': 'USD'
            },
            'snapshot': {
                'bid': 75.5,
                'offer': 75.6,
                'marketStatus': 'TRADEABLE'
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = CapitalClient()
        details = client.get_market_details('CRUDE_OIL')
        
        assert 'instrument' in details
        assert details['instrument']['epic'] == 'CRUDE_OIL'
    
    @patch('src.capital_client.requests.Session.get')
    def test_get_prices(self, mock_get):
        """Test getting price data"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'prices': [
                {
                    'snapshotTimeUTC': '2024-01-01T00:00:00',
                    'closePrice': {'bid': 75.5, 'ask': 75.6},
                    'openPrice': {'bid': 75.4, 'ask': 75.5},
                    'highPrice': {'bid': 75.7, 'ask': 75.8},
                    'lowPrice': {'bid': 75.3, 'ask': 75.4},
                    'lastTradedVolume': 1000
                },
                {
                    'snapshotTimeUTC': '2024-01-01T01:00:00',
                    'closePrice': {'bid': 75.7, 'ask': 75.8},
                    'openPrice': {'bid': 75.5, 'ask': 75.6},
                    'highPrice': {'bid': 75.9, 'ask': 76.0},
                    'lowPrice': {'bid': 75.5, 'ask': 75.6},
                    'lastTradedVolume': 1200
                }
            ],
            'instrumentType': 'COMMODITIES'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = CapitalClient()
        df = client.get_prices('CRUDE_OIL', resolution='HOUR')
        
        assert not df.empty
        assert len(df) == 2
        assert 'bid' in df.columns
        assert 'ask' in df.columns
        assert 'mid_price' in df.columns
        assert isinstance(df.index, pd.DatetimeIndex)
        
        # Check mid price calculation
        assert df.iloc[0]['mid_price'] == (75.5 + 75.6) / 2
    
    @patch('src.capital_client.requests.Session.get')
    def test_get_prices_empty(self, mock_get):
        """Test handling empty price response"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'prices': [],
            'instrumentType': 'COMMODITIES'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = CapitalClient()
        df = client.get_prices('INVALID_EPIC')
        
        assert df.empty
    
    @patch('src.capital_client.time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test that rate limiting is applied"""
        client = CapitalClient()
        
        # First request should not sleep
        client._rate_limit()
        assert mock_sleep.call_count == 0
        
        # Second request immediately after should sleep
        client._rate_limit()
        assert mock_sleep.call_count == 1
    
    @patch('src.capital_client.requests.Session.get')
    @patch('src.capital_client.time.time')
    def test_chunked_historical_data(self, mock_time, mock_get):
        """Test chunked historical data retrieval"""
        # Mock time to avoid actual delays
        mock_time.return_value = 1000
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'prices': [
                {
                    'snapshotTimeUTC': '2024-01-01T00:00:00',
                    'closePrice': {'bid': 75.5, 'ask': 75.6},
                    'lastTradedVolume': 1000
                }
            ],
            'instrumentType': 'COMMODITIES'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = CapitalClient()
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        
        df = client.get_historical_prices_chunked(
            epic='CRUDE_OIL',
            start_date=start_date,
            end_date=end_date,
            resolution='HOUR',
            chunk_days=2
        )
        
        assert not df.empty
        # Should have made multiple API calls for chunks
        assert mock_get.call_count >= 2
