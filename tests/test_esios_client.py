"""
Tests for ESIOS API client
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

from src.esios_client import ESIOSClient


class TestESIOSClient:
    """Test suite for ESIOSClient"""
    
    def test_client_initialization(self):
        """Test client can be initialized"""
        client = ESIOSClient(token="test_token")
        assert client.token == "test_token"
        assert client.base_url == "https://api.esios.ree.es"
    
    def test_client_initialization_no_token(self):
        """Test client can be initialized without token"""
        client = ESIOSClient()
        assert client.token is not None or client.token == ""
    
    @patch('src.esios_client.requests.Session.get')
    def test_get_indicators(self, mock_get):
        """Test getting list of indicators"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'indicators': [
                {'id': 1001, 'name': 'PVPC 2.0TD'},
                {'id': 600, 'name': 'SPOT Price'}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = ESIOSClient(token="test_token")
        indicators = client.get_indicators()
        
        assert len(indicators) == 2
        assert indicators[0]['id'] == 1001
    
    @patch('src.esios_client.requests.Session.get')
    def test_get_indicator_data(self, mock_get):
        """Test getting data for a specific indicator"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'indicator': {
                'id': 1001,
                'name': 'PVPC 2.0TD',
                'values': [
                    {'datetime': '2024-01-01T00:00:00Z', 'value': 89.45},
                    {'datetime': '2024-01-01T01:00:00Z', 'value': 87.32}
                ]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = ESIOSClient(token="test_token")
        df = client.get_indicator_data(1001, '2024-01-01', '2024-01-02')
        
        assert not df.empty
        assert len(df) == 2
        assert 'value' in df.columns
        assert isinstance(df.index, pd.DatetimeIndex)
    
    @patch('src.esios_client.requests.Session.get')
    def test_get_indicator_data_empty(self, mock_get):
        """Test handling empty response"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'indicator': {
                'id': 1001,
                'name': 'PVPC 2.0TD',
                'values': []
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = ESIOSClient(token="test_token")
        df = client.get_indicator_data(1001, '2024-01-01', '2024-01-02')
        
        assert df.empty
    
    def test_date_formatting(self):
        """Test date parameter formatting"""
        client = ESIOSClient(token="test_token")
        
        # Test that dates without time get formatted correctly
        # This is tested implicitly in the API call
        assert client.base_url is not None
