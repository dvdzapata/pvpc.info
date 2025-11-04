"""
Data collector for PVPC historical prices
"""
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Optional

from .esios_client import ESIOSClient
from .config import DATA_DIR, INDICATORS, DEFAULT_START_DATE, DEFAULT_TIMEZONE

logger = logging.getLogger(__name__)


class PVPCDataCollector:
    """Collector for PVPC historical data"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the data collector
        
        Args:
            api_token: Optional API token for ESIOS
        """
        self.client = ESIOSClient(token=api_token)
        self.data_dir = DATA_DIR
    
    def collect_historical_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        indicator_name: str = 'pvpc_2.0TD',
        save_to_file: bool = True
    ) -> pd.DataFrame:
        """
        Collect historical PVPC data
        
        Args:
            start_date: Start date (YYYY-MM-DD). Defaults to DEFAULT_START_DATE
            end_date: End date (YYYY-MM-DD). Defaults to yesterday
            indicator_name: Name of the indicator to collect
            save_to_file: Whether to save data to CSV file
        
        Returns:
            DataFrame with collected data
        """
        # Set default dates
        if start_date is None:
            start_date = DEFAULT_START_DATE
        
        if end_date is None:
            # Use timezone-aware datetime for consistency
            import pytz
            tz = pytz.timezone(DEFAULT_TIMEZONE)
            end_date = (datetime.now(tz) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get indicator ID
        indicator_id = INDICATORS.get(indicator_name)
        if indicator_id is None:
            raise ValueError(f"Unknown indicator: {indicator_name}")
        
        logger.info(f"Collecting data for {indicator_name} from {start_date} to {end_date}")
        
        # Collect data in chunks
        df = self.client.get_historical_data_chunked(
            indicator_id=indicator_id,
            start_date=start_date,
            end_date=end_date,
            chunk_days=365,
            delay_seconds=1.0
        )
        
        if df.empty:
            logger.warning("No data collected")
            return df
        
        # Process data
        df = self._process_data(df, indicator_name)
        
        # Save to file
        if save_to_file:
            self._save_to_csv(df, indicator_name, start_date, end_date)
        
        return df
    
    def _process_data(self, df: pd.DataFrame, indicator_name: str) -> pd.DataFrame:
        """
        Process and clean the collected data
        
        Args:
            df: Raw data from API
            indicator_name: Name of the indicator
        
        Returns:
            Processed DataFrame
        """
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'datetime' in df.columns:
                df.set_index('datetime', inplace=True)
        
        # Localize to Madrid timezone if not already
        if df.index.tz is None:
            df.index = df.index.tz_localize(DEFAULT_TIMEZONE)
        
        # Sort by datetime
        df.sort_index(inplace=True)
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Rename value column for clarity
        if 'value' in df.columns:
            df.rename(columns={'value': 'price_eur_mwh'}, inplace=True)
        
        logger.info(f"Processed {len(df)} records")
        return df
    
    def _save_to_csv(
        self,
        df: pd.DataFrame,
        indicator_name: str,
        start_date: str,
        end_date: str
    ):
        """
        Save data to CSV file
        
        Args:
            df: DataFrame to save
            indicator_name: Name of the indicator
            start_date: Start date of data
            end_date: End date of data
        """
        filename = f"{indicator_name}_{start_date}_{end_date}.csv"
        filepath = self.data_dir / filename
        
        df.to_csv(filepath)
        logger.info(f"Data saved to {filepath}")
        
        # Also save a "latest" version
        latest_filename = f"{indicator_name}_latest.csv"
        latest_filepath = self.data_dir / latest_filename
        df.to_csv(latest_filepath)
        logger.info(f"Latest data saved to {latest_filepath}")
    
    def collect_all_indicators(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        Collect data for all configured indicators
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dictionary with indicator names as keys and DataFrames as values
        """
        results = {}
        
        for indicator_name in INDICATORS.keys():
            try:
                logger.info(f"Collecting data for {indicator_name}")
                df = self.collect_historical_data(
                    start_date=start_date,
                    end_date=end_date,
                    indicator_name=indicator_name,
                    save_to_file=True
                )
                results[indicator_name] = df
            except Exception as e:
                logger.error(f"Error collecting data for {indicator_name}: {e}")
                results[indicator_name] = None
        
        return results
    
    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """
        Get summary statistics of the collected data
        
        Args:
            df: DataFrame with collected data
        
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {}
        
        price_col = 'price_eur_mwh' if 'price_eur_mwh' in df.columns else 'value'
        
        summary = {
            'start_date': df.index.min().strftime('%Y-%m-%d %H:%M:%S'),
            'end_date': df.index.max().strftime('%Y-%m-%d %H:%M:%S'),
            'total_records': len(df),
            'mean_price': df[price_col].mean() if price_col in df.columns else None,
            'min_price': df[price_col].min() if price_col in df.columns else None,
            'max_price': df[price_col].max() if price_col in df.columns else None,
            'std_price': df[price_col].std() if price_col in df.columns else None,
        }
        
        return summary
