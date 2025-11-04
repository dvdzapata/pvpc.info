"""
Client for interacting with the ESIOS API (Red Eléctrica de España)
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
import time

from .config import ESIOS_API_TOKEN, ESIOS_BASE_URL, DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)


class ESIOSClient:
    """Client for the ESIOS API to retrieve electricity market data"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the ESIOS API client
        
        Args:
            token: API token for authentication. If not provided, uses config.
        
        Raises:
            ValueError: If no API token is provided
        """
        self.token = token or ESIOS_API_TOKEN
        if not self.token:
            raise ValueError(
                "No API token provided. Please:\n"
                "  1. Set ESIOS_API_TOKEN in your .env file, or\n"
                "  2. Pass token parameter to ESIOSClient(), or\n"
                "  3. Get a free token at https://www.esios.ree.es"
            )
        
        self.base_url = ESIOS_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Host': 'api.esios.ree.es',
            'x-api-key': self.token
        })
    
    def get_indicators(self) -> List[Dict]:
        """
        Get list of available indicators
        
        Returns:
            List of indicator metadata
        """
        url = f"{self.base_url}/indicators"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('indicators', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching indicators: {e}")
            raise
    
    def get_indicator_data(
        self,
        indicator_id: int,
        start_date: str,
        end_date: str,
        time_trunc: str = 'hour'
    ) -> pd.DataFrame:
        """
        Get data for a specific indicator
        
        Args:
            indicator_id: ID of the indicator to retrieve
            start_date: Start date in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM'
            end_date: End date in format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM'
            time_trunc: Time truncation ('hour', 'day', etc.)
        
        Returns:
            DataFrame with the indicator data
        """
        url = f"{self.base_url}/indicators/{indicator_id}"
        
        # Format dates for API
        if 'T' not in start_date:
            start_date = f"{start_date}T00:00:00"
        if 'T' not in end_date:
            end_date = f"{end_date}T23:59:59"
        
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'time_trunc': time_trunc
        }
        
        try:
            logger.info(f"Fetching indicator {indicator_id} from {start_date} to {end_date}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Parse the response into a DataFrame
            if 'indicator' in data and 'values' in data['indicator']:
                values = data['indicator']['values']
                if not values:
                    logger.warning(f"No data returned for indicator {indicator_id}")
                    return pd.DataFrame()
                
                df = pd.DataFrame(values)
                
                # Convert datetime strings to datetime objects
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df.set_index('datetime', inplace=True)
                
                # Add metadata
                df['indicator_id'] = indicator_id
                if 'indicator' in data:
                    df['indicator_name'] = data['indicator'].get('name', '')
                
                logger.info(f"Retrieved {len(df)} records for indicator {indicator_id}")
                return df
            else:
                logger.warning(f"Unexpected response format for indicator {indicator_id}")
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching indicator {indicator_id}: {e}")
            raise
    
    def get_pvpc_prices(
        self,
        start_date: str,
        end_date: str,
        indicator_id: int = 1001
    ) -> pd.DataFrame:
        """
        Get PVPC prices for a date range
        
        Args:
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
            indicator_id: PVPC indicator ID (default: 1001 for 2.0TD)
        
        Returns:
            DataFrame with PVPC prices
        """
        return self.get_indicator_data(indicator_id, start_date, end_date)
    
    def get_historical_data_chunked(
        self,
        indicator_id: int,
        start_date: str,
        end_date: str,
        chunk_days: int = 365,
        delay_seconds: float = 1.0
    ) -> pd.DataFrame:
        """
        Get historical data in chunks to avoid API limits
        
        Args:
            indicator_id: ID of the indicator
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
            chunk_days: Number of days per API request
            delay_seconds: Delay between requests to respect rate limits
        
        Returns:
            Combined DataFrame with all data
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        all_data = []
        current_start = start
        
        while current_start < end:
            current_end = min(current_start + timedelta(days=chunk_days), end)
            
            try:
                chunk_data = self.get_indicator_data(
                    indicator_id,
                    current_start.strftime('%Y-%m-%d'),
                    current_end.strftime('%Y-%m-%d')
                )
                
                if not chunk_data.empty:
                    all_data.append(chunk_data)
                
                # Continue from where this chunk ended (no gap, no overlap)
                current_start = current_end
                
                # Rate limiting
                if current_start < end:
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                logger.error(f"Error fetching chunk {current_start} to {current_end}: {e}")
                # Continue from where this chunk would have ended to avoid gaps
                current_start = current_end
        
        if all_data:
            return pd.concat(all_data, axis=0)
        else:
            return pd.DataFrame()
