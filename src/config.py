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

# Capital.com API Configuration
CAPITAL_BASE_URL = 'https://api-capital.backend-capital.com/api/v1'

# Commodity EPICs for Capital.com
COMMODITY_EPICS = {
    # Real-time CFDs
    'crude_oil_rt': 'CRUDE_OIL',
    'natural_gas_rt': 'NATURALGAS',
    'brent_oil_rt': 'BRENT_CRUDE_OIL',
    'gas_london_rt': 'NATURAL_GAS',
    
    # Futures contracts - Carbon emissions
    'carbon_dec_2025': 'EUA.D.PHHZ5.C.IP',
    
    # Futures contracts - Natural Gas
    'gas_eu_ttf_dec_2025': 'NATGAS.F.TTF.Z5.IP',
    'gas_eu_ttf_jan_2026': 'NATGAS.F.TTF.F6.IP',
    'gas_eu_ttf_feb_2026': 'NATGAS.F.TTF.G6.IP',
    
    # Futures contracts - Brent Oil
    'brent_oil_jan_2026': 'OIL_BRENT.F.LCO.F6.IP',
    'brent_oil_feb_2026': 'OIL_BRENT.F.LCO.G6.IP',
    
    # Futures contracts - Crude Oil
    'crude_oil_dec_2025': 'OIL_CRUDE.F.CL.Z5.IP',
    'crude_oil_jan_2026': 'OIL_CRUDE.F.CL.F6.IP',
    
    # Futures contracts - Gas London
    'gas_london_nov_2025': 'NATURAL_GAS.F.NG.X5.IP',
}

# Capital.com rate limiting (requests per second)
CAPITAL_RATE_LIMIT = 0.5  # 2 requests per second max
CAPITAL_MAX_HISTORICAL_DAYS = 730  # 2 years maximum
