"""
Tests for ESIOS Data Collector
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

from src.esios_data_collector import ESIOSDataCollector


class TestESIOSDataCollector:
    """Test suite for ESIOSDataCollector"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_indicators_file(self, temp_dir):
        """Create a sample indicators file"""
        indicators_data = {
            "indicators": [
                {
                    "id": 1001,
                    "name": "PVPC 2.0TD",
                    "short_name": "PVPC 2.0TD",
                    "description": "Precio PVPC tarifa 2.0TD"
                },
                {
                    "id": 544,
                    "name": "Demanda prevista",
                    "short_name": "Demanda prevista",
                    "description": "Prevision de demanda electrica"
                },
                {
                    "id": 12,
                    "name": "Generación programada PBF Eólica terrestre",
                    "short_name": "Eólica terrestre",
                    "description": "Generacion eolica programada"
                }
            ],
            "meta": {"size": 3}
        }
        
        filepath = temp_dir / "indicators.json"
        with open(filepath, 'w') as f:
            json.dump(indicators_data, f)
        
        return filepath
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_collector_initialization(self, mock_db, mock_client, temp_dir):
        """Test collector can be initialized"""
        collector = ESIOSDataCollector(
            api_token="test_token",
            database_url="sqlite:///:memory:",
            checkpoint_dir=temp_dir
        )
        
        assert collector.checkpoint_dir == temp_dir
        assert collector.max_requests_per_minute == 50
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_parse_indicators_file(self, mock_db, mock_client, sample_indicators_file):
        """Test parsing indicators file"""
        collector = ESIOSDataCollector(api_token="test_token")
        
        indicators = collector.parse_indicators_file(sample_indicators_file)
        
        assert len(indicators) == 3
        assert indicators[0]['id'] == 1001
        assert indicators[1]['id'] == 544
        assert indicators[2]['id'] == 12
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_categorize_indicator_price(self, mock_db, mock_client):
        """Test categorization of price indicator"""
        collector = ESIOSDataCollector(api_token="test_token")
        
        indicator = {
            "id": 1001,
            "name": "PVPC 2.0TD",
            "short_name": "PVPC",
            "description": "Precio voluntario pequeño consumidor"
        }
        
        category = collector.categorize_indicator(indicator)
        assert category == "price"
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_categorize_indicator_demand(self, mock_db, mock_client):
        """Test categorization of demand indicator"""
        collector = ESIOSDataCollector(api_token="test_token")
        
        indicator = {
            "id": 544,
            "name": "Demanda prevista",
            "short_name": "Demanda",
            "description": "Prevision de consumo electrico"
        }
        
        category = collector.categorize_indicator(indicator)
        assert category == "demand"
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_categorize_indicator_production(self, mock_db, mock_client):
        """Test categorization of production indicator"""
        collector = ESIOSDataCollector(api_token="test_token")
        
        indicator = {
            "id": 12,
            "name": "Generación eólica",
            "short_name": "Eólica",
            "description": "Generacion de energia eolica"
        }
        
        category = collector.categorize_indicator(indicator)
        assert category == "production"
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_assign_priority_price(self, mock_db, mock_client):
        """Test priority assignment for price indicators"""
        collector = ESIOSDataCollector(api_token="test_token")
        
        indicator = {
            "id": 1001,
            "name": "PVPC 2.0TD",
            "short_name": "PVPC"
        }
        
        priority = collector.assign_priority(indicator, "price")
        assert priority == 1  # Critical priority
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_assign_priority_demand(self, mock_db, mock_client):
        """Test priority assignment for demand indicators"""
        collector = ESIOSDataCollector(api_token="test_token")
        
        indicator = {
            "id": 544,
            "name": "Demanda prevista",
            "short_name": "Demanda prevista"
        }
        
        priority = collector.assign_priority(indicator, "demand")
        assert priority == 1  # Critical priority
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_assign_priority_production(self, mock_db, mock_client):
        """Test priority assignment for production indicators"""
        collector = ESIOSDataCollector(api_token="test_token")
        
        indicator = {
            "id": 12,
            "name": "Solar fotovoltaica",
            "short_name": "Solar"
        }
        
        priority = collector.assign_priority(indicator, "production")
        assert priority == 2  # Important priority
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_generate_indicators_catalog(self, mock_db, mock_client, sample_indicators_file, temp_dir):
        """Test catalog generation"""
        collector = ESIOSDataCollector(api_token="test_token")
        
        output_file = temp_dir / "catalog.json"
        indicators = collector.generate_indicators_catalog(
            sample_indicators_file,
            output_file
        )
        
        assert len(indicators) == 3
        assert output_file.exists()
        
        # Check output file structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert 'indicators' in data
        assert data['metadata']['total_indicators'] == 3
        assert 'categories' in data['metadata']
        
        # Check indicator structure
        for ind in data['indicators']:
            assert 'id' in ind
            assert 'name' in ind
            assert 'category' in ind
            assert 'priority' in ind
            assert 'justification' in ind
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_checkpoint_save_and_load(self, mock_db, mock_client, temp_dir):
        """Test checkpoint save and load"""
        collector = ESIOSDataCollector(
            api_token="test_token",
            checkpoint_dir=temp_dir
        )
        
        # Save checkpoint
        checkpoint_data = {
            'completed': [1, 2, 3, 4, 5],
            'last_updated': '2024-01-01T00:00:00'
        }
        collector.save_checkpoint('test_checkpoint', checkpoint_data)
        
        # Load checkpoint
        loaded_data = collector.load_checkpoint('test_checkpoint')
        
        assert loaded_data is not None
        assert loaded_data['completed'] == [1, 2, 3, 4, 5]
        assert loaded_data['last_updated'] == '2024-01-01T00:00:00'
    
    @patch('src.esios_data_collector.ESIOSClient')
    @patch('src.esios_data_collector.DatabaseManager')
    def test_checkpoint_load_nonexistent(self, mock_db, mock_client, temp_dir):
        """Test loading non-existent checkpoint"""
        collector = ESIOSDataCollector(
            api_token="test_token",
            checkpoint_dir=temp_dir
        )
        
        loaded_data = collector.load_checkpoint('nonexistent')
        assert loaded_data is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
