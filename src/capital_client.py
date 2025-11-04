"""
Client for interacting with the Capital.com API for commodity market data
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
import time

from .config import CAPITAL_BASE_URL, CAPITAL_RATE_LIMIT, DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)

# Maximum data points that can be requested from the API in a single call
MAX_API_POINTS = 10000


class CapitalClient:
    """Client for the Capital.com API to retrieve commodity market data"""
    
    def __init__(self):
        """
        Initialize the Capital.com API client
        
        Note: Capital.com API does not require authentication for market data
        """
        self.base_url = CAPITAL_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        self.last_request_time = 0
        self.rate_limit_delay = CAPITAL_RATE_LIMIT
    
    def _rate_limit(self):
        """Implement rate limiting to respect API constraints"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_markets(self, epic: Optional[str] = None) -> List[Dict]:
        """
        Get market data for one or all markets
        
        Args:
            epic: Optional EPIC code to get specific market data
        
        Returns:
            List of market data dictionaries
        """
        self._rate_limit()
        
        url = f"{self.base_url}/markets"
        params = {}
        if epic:
            params['epic'] = epic
        
        try:
            logger.debug(f"Fetching markets data{' for ' + epic if epic else ''}")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            markets = data.get('markets', [])
            logger.info(f"Retrieved {len(markets)} market(s)")
            return markets
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching markets: {e}")
            raise
    
    def get_market_details(self, epic: str) -> Dict:
        """
        Get detailed information for a specific market
        
        Args:
            epic: EPIC code of the market
        
        Returns:
            Dictionary with market details including instrument, dealing rules, and snapshot
        """
        self._rate_limit()
        
        url = f"{self.base_url}/markets/{epic}"
        
        try:
            logger.debug(f"Fetching market details for {epic}")
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Retrieved market details for {epic}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching market details for {epic}: {e}")
            raise
    
    def get_prices(
        self,
        epic: str,
        resolution: str = 'MINUTE',
        max_points: int = 1000,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical price data for a specific market
        
        Args:
            epic: EPIC code of the market
            resolution: Time resolution (MINUTE, HOUR, DAY, WEEK)
            max_points: Maximum number of data points to retrieve (default 1000)
            from_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SS)
            to_date: End date in ISO format (YYYY-MM-DDTHH:MM:SS)
        
        Returns:
            DataFrame with historical price data
        """
        self._rate_limit()
        
        url = f"{self.base_url}/prices/{epic}"
        
        params = {
            'resolution': resolution,
            'max': max_points
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        
        try:
            logger.debug(f"Fetching prices for {epic} (resolution: {resolution}, max: {max_points})")
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Parse the response into a DataFrame
            prices = data.get('prices', [])
            if not prices:
                logger.warning(f"No price data returned for {epic}")
                return pd.DataFrame()
            
            df = pd.DataFrame(prices)
            
            # Convert snapshotTimeUTC to datetime
            if 'snapshotTimeUTC' in df.columns:
                df['datetime'] = pd.to_datetime(df['snapshotTimeUTC'])
                df.set_index('datetime', inplace=True)
            
            # Extract bid and ask prices from nested dictionaries
            if 'closePrice' in df.columns:
                df['bid'] = df['closePrice'].apply(lambda x: x.get('bid') if isinstance(x, dict) else None)
                df['ask'] = df['closePrice'].apply(lambda x: x.get('ask') if isinstance(x, dict) else None)
                df['mid_price'] = (df['bid'] + df['ask']) / 2
            
            # Add metadata
            df['epic'] = epic
            df['instrument_type'] = data.get('instrumentType', '')
            
            logger.info(f"Retrieved {len(df)} price records for {epic}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching prices for {epic}: {e}")
            raise
    
    def get_historical_prices_chunked(
        self,
        epic: str,
        start_date: datetime,
        end_date: datetime,
        resolution: str = 'HOUR',
        chunk_days: int = 30
    ) -> pd.DataFrame:
        """
        Get historical price data in chunks to handle large date ranges
        
        Args:
            epic: EPIC code of the market
            start_date: Start datetime
            end_date: End datetime
            resolution: Time resolution (MINUTE, HOUR, DAY, WEEK)
            chunk_days: Number of days per API request
        
        Returns:
            Combined DataFrame with all price data
        """
        all_data = []
        current_start = start_date
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=chunk_days), end_date)
            
            try:
                # Calculate max points based on resolution and date range
                if resolution == 'MINUTE':
                    max_points = min(chunk_days * 24 * 60, MAX_API_POINTS)
                elif resolution == 'HOUR':
                    max_points = min(chunk_days * 24, MAX_API_POINTS)
                elif resolution == 'DAY':
                    max_points = min(chunk_days, MAX_API_POINTS)
                else:
                    max_points = 1000
                
                chunk_data = self.get_prices(
                    epic=epic,
                    resolution=resolution,
                    max_points=max_points,
                    from_date=current_start.isoformat(),
                    to_date=current_end.isoformat()
                )
                
                if not chunk_data.empty:
                    all_data.append(chunk_data)
                
                logger.info(f"Collected chunk: {current_start.date()} to {current_end.date()}")
                
                # Move to next chunk
                current_start = current_end + timedelta(seconds=1)
                
            except Exception as e:
                logger.error(f"Error fetching chunk {current_start} to {current_end}: {e}")
                # Continue from where this chunk would have ended
                current_start = current_end + timedelta(seconds=1)
        
        if all_data:
            combined_df = pd.concat(all_data, axis=0)
            # Remove duplicates and sort
            combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
            combined_df.sort_index(inplace=True)
            return combined_df
        else:
            return pd.DataFrame()
