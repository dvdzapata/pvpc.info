"""
Configuration management for PVPC data collection
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv('DATA_DIR', BASE_DIR / 'data'))
LOG_DIR = Path(os.getenv('LOG_DIR', BASE_DIR / 'logs'))

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ESIOS API Configuration
ESIOS_API_TOKEN = os.getenv('ESIOS_API_TOKEN', '')
ESIOS_BASE_URL = 'https://api.esios.ree.es'

# PVPC Indicator IDs in ESIOS
# These are the main indicators for PVPC prices
INDICATORS = {
    'pvpc_2.0TD': 1001,  # PVPC 2.0TD (most common residential tariff)
    'pvpc_spot': 600,    # Day-ahead market price (SPOT)
    'pvpc_base': 1739,   # PVPC base price
}

# Data collection settings
DEFAULT_START_DATE = '2021-01-01'  # Start of historical data collection
DEFAULT_TIMEZONE = 'Europe/Madrid'
