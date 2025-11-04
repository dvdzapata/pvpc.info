"""
Tests for AEMET API client
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime
import requests

from src.aemet_client import AEMETClient


class TestAEMETClient:
    """Test suite for AEMETClient"""
    
    def test_client_initialization(self):
        """Test client can be initialized"""
        client = AEMETClient(token="test_token")
        assert client.token == "test_token"
        assert client.base_url == "https://opendata.aemet.es/opendata/api"
    
    def test_client_initialization_no_token(self):
        """Test client raises ValueError when no token provided"""
        with pytest.raises(ValueError, match="No API token provided"):
            AEMETClient(token='')
    
    @patch('src.aemet_client.requests.Session.get')
    def test_make_request_with_data_url(self, mock_get):
        """Test _make_request handles two-step API response"""
        # First response with data URL
        mock_response_1 = Mock()
        mock_response_1.json.return_value = {
            'datos': 'https://opendata.aemet.es/data/file.json',
            'estado': 200
        }
        mock_response_1.raise_for_status = Mock()
        
        # Second response with actual data
        mock_response_2 = Mock()
        mock_response_2.json.return_value = [
            {'fecha': '2021-01-01', 'tmed': '3,2'}
        ]
        mock_response_2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response_1, mock_response_2]
        
        client = AEMETClient(token="test_token")
        result = client._make_request("test/endpoint")
        
        assert len(result) == 1
        assert result[0]['fecha'] == '2021-01-01'
        assert mock_get.call_count == 2
    
    @patch('src.aemet_client.requests.Session.get')
    def test_make_request_direct_data(self, mock_get):
        """Test _make_request handles direct data response"""
        mock_response = Mock()
        mock_response.json.return_value = {'data': 'direct'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = AEMETClient(token="test_token")
        result = client._make_request("test/endpoint")
        
        assert result == {'data': 'direct'}
        assert mock_get.call_count == 1
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_climatological_series(self, mock_request):
        """Test getting climatological series data"""
        mock_request.return_value = [
            {
                'fecha': '2021-01-01',
                'indicativo': '9091R',
                'nombre': 'VITORIA-GASTEIZ AEROPUERTO',
                'tmed': '3,2',
                'prec': '20,1'
            }
        ]
        
        client = AEMETClient(token="test_token")
        data = client.get_climatological_series('2021-01-01', '2021-03-01')
        
        assert len(data) == 1
        assert data[0]['fecha'] == '2021-01-01'
        mock_request.assert_called_once()
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_climatological_series_chunking(self, mock_request):
        """Test that long date ranges are chunked into 6-month periods"""
        mock_request.return_value = [{'fecha': '2021-01-01'}]
        
        client = AEMETClient(token="test_token")
        # Request 13 months of data (should result in 3 API calls)
        data = client.get_climatological_series('2021-01-01', '2022-02-01')
        
        # Should have made 3 calls (6 months + 6 months + 1 month)
        assert mock_request.call_count == 3
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_normal_values(self, mock_request):
        """Test getting normal climatological values"""
        mock_request.return_value = {
            'indicativo': '8178D',
            'w_racha_max': '23.3',
            'mes': '01'
        }
        
        client = AEMETClient(token="test_token")
        data = client.get_normal_values('8178D')
        
        assert data['indicativo'] == '8178D'
        assert 'w_racha_max' in data
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_monthly_climatology(self, mock_request):
        """Test getting monthly climatology data"""
        mock_request.return_value = {
            'indicativo': '5402',
            'p_max': '28.8(15)',
            'fecha': '2024-10'
        }
        
        client = AEMETClient(token="test_token")
        data = client.get_monthly_climatology(2024, 10, '5402')
        
        assert data['indicativo'] == '5402'
        assert data['fecha'] == '2024-10'
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_temperature_extremes(self, mock_request):
        """Test getting temperature extremes"""
        mock_request.return_value = {
            'indicativo': '5402',
            'nombre': 'CÓRDOBA AEROPUERTO',
            'temMin': ['-82', '-50'],
            'temMax': ['235', '278']
        }
        
        client = AEMETClient(token="test_token")
        data = client.get_temperature_extremes('5402')
        
        assert data['indicativo'] == '5402'
        assert 'temMin' in data
        assert 'temMax' in data
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_precipitation_extremes(self, mock_request):
        """Test getting precipitation extremes"""
        mock_request.return_value = {
            'indicativo': '5402',
            'precMaxDia': ['791', '607'],
            'precMaxMen': ['2934', '2670']
        }
        
        client = AEMETClient(token="test_token")
        data = client.get_precipitation_extremes('5402')
        
        assert data['indicativo'] == '5402'
        assert 'precMaxDia' in data
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_wind_extremes(self, mock_request):
        """Test getting wind extremes"""
        mock_request.return_value = {
            'indicativo': '5402',
            'rachMax': ['82', '84', '91']
        }
        
        client = AEMETClient(token="test_token")
        data = client.get_wind_extremes('5402')
        
        assert data['indicativo'] == '5402'
        assert 'rachMax' in data
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_weather_prediction(self, mock_request):
        """Test getting weather prediction"""
        mock_request.return_value = {
            'nombre': 'Arraia-Maeztu',
            'provincia': 'Araba/Álava',
            'prediccion': {
                'dia': [{'temperatura': [{'value': '7'}]}]
            }
        }
        
        client = AEMETClient(token="test_token")
        data = client.get_weather_prediction('01037')
        
        assert data['nombre'] == 'Arraia-Maeztu'
        assert 'prediccion' in data
    
    @patch('src.aemet_client.AEMETClient._make_request')
    def test_get_stations_list(self, mock_request):
        """Test getting stations list"""
        mock_request.return_value = [
            {
                'indicativo': 'B051A',
                'nombre': 'SÓLLER, PUERTO',
                'provincia': 'ILLES BALEARS'
            }
        ]
        
        client = AEMETClient(token="test_token")
        data = client.get_stations_list()
        
        assert len(data) == 1
        assert data[0]['indicativo'] == 'B051A'
    
    def test_climatological_to_dataframe(self):
        """Test converting climatological data to DataFrame"""
        data = [
            {
                'fecha': '2021-01-01',
                'indicativo': '9091R',
                'tmed': '3,2',
                'prec': '20,1',
                'tmin': '-0,1',
                'tmax': '6,4'
            },
            {
                'fecha': '2021-01-02',
                'indicativo': '9091R',
                'tmed': '4,5',
                'prec': '15,0',
                'tmin': '1,2',
                'tmax': '7,8'
            }
        ]
        
        client = AEMETClient(token="test_token")
        df = client.climatological_to_dataframe(data)
        
        assert not df.empty
        assert len(df) == 2
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df['tmed'].dtype == float
        assert df.loc['2021-01-01', 'tmed'] == 3.2
        assert df.loc['2021-01-01', 'prec'] == 20.1
    
    def test_climatological_to_dataframe_empty(self):
        """Test converting empty data"""
        client = AEMETClient(token="test_token")
        df = client.climatological_to_dataframe([])
        
        assert df.empty
    
    @patch('src.aemet_client.requests.Session.get')
    def test_error_handling(self, mock_get):
        """Test error handling in API requests"""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        client = AEMETClient(token="test_token")
        with pytest.raises(requests.exceptions.RequestException):
            client._make_request("test/endpoint")
