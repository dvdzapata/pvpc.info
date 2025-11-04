"""
Data collector for commodity price data from Capital.com
"""
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Optional, Dict, List
import pytz

from .capital_client import CapitalClient
from .database import DatabaseManager, CommodityMetadata
from .config import (
    DATA_DIR, 
    COMMODITY_EPICS, 
    DEFAULT_TIMEZONE,
    CAPITAL_MAX_HISTORICAL_DAYS
)

logger = logging.getLogger(__name__)


class CommodityDataCollector:
    """Collector for commodity historical price data"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the commodity data collector
        
        Args:
            database_url: Optional database connection URL
        """
        self.client = CapitalClient()
        self.db = DatabaseManager(database_url)
        self.data_dir = DATA_DIR
        
        # Create database tables
        self.db.create_tables()
    
    def collect_historical_data(
        self,
        epic: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        resolution: str = 'HOUR',
        save_to_file: bool = True,
        save_to_db: bool = True
    ) -> pd.DataFrame:
        """
        Collect historical price data for a commodity
        
        Args:
            epic: EPIC code of the commodity
            start_date: Start date for data collection
            end_date: End date for data collection
            resolution: Time resolution (MINUTE, HOUR, DAY, WEEK)
            save_to_file: Whether to save data to CSV
            save_to_db: Whether to save data to database
        
        Returns:
            DataFrame with collected data
        """
        # Set default dates
        if end_date is None:
            tz = pytz.timezone(DEFAULT_TIMEZONE)
            end_date = datetime.now(tz).replace(tzinfo=None)
        
        if start_date is None:
            # Default to maximum historical range (2 years)
            start_date = end_date - timedelta(days=CAPITAL_MAX_HISTORICAL_DAYS)
        
        logger.info(f"Collecting data for {epic} from {start_date.date()} to {end_date.date()}")
        logger.info(f"Resolution: {resolution}")
        
        # Validate data quality before collection
        self._validate_date_range(start_date, end_date)
        
        # Collect data in chunks
        df = self.client.get_historical_prices_chunked(
            epic=epic,
            start_date=start_date,
            end_date=end_date,
            resolution=resolution,
            chunk_days=30  # 30-day chunks to manage API limits
        )
        
        if df.empty:
            logger.warning(f"No data collected for {epic}")
            return df
        
        # Validate data quality
        df = self._validate_and_clean_data(df, epic)
        
        # Get market details for metadata
        try:
            market_details = self.client.get_market_details(epic)
            instrument = market_details.get('instrument', {})
        except Exception as e:
            logger.warning(f"Could not fetch market details for {epic}: {e}")
            instrument = {}
        
        # Save to database
        if save_to_db:
            self._save_to_database(df, epic, resolution, instrument)
        
        # Save to file
        if save_to_file:
            self._save_to_csv(df, epic, start_date, end_date, resolution)
        
        return df
    
    def _validate_date_range(self, start_date: datetime, end_date: datetime):
        """
        Validate date range parameters
        
        Args:
            start_date: Start date
            end_date: End date
        
        Raises:
            ValueError: If date range is invalid
        """
        if start_date >= end_date:
            raise ValueError(f"Start date must be before end date")
        
        date_range_days = (end_date - start_date).days
        if date_range_days > CAPITAL_MAX_HISTORICAL_DAYS:
            logger.warning(
                f"Date range ({date_range_days} days) exceeds maximum "
                f"({CAPITAL_MAX_HISTORICAL_DAYS} days). Data may be incomplete."
            )
    
    def _validate_and_clean_data(self, df: pd.DataFrame, epic: str) -> pd.DataFrame:
        """
        Validate and clean the collected data
        
        Args:
            df: Raw data from API
            epic: EPIC code
        
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        initial_count = len(df)
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning(f"Index is not DatetimeIndex for {epic}")
        
        # Sort by datetime
        df.sort_index(inplace=True)
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Check for missing critical fields
        if 'bid' not in df.columns or 'ask' not in df.columns:
            logger.warning(f"Missing bid/ask columns for {epic}")
        
        # Remove rows with null prices
        if 'mid_price' in df.columns:
            df = df.dropna(subset=['mid_price'])
        
        # Check for outliers (prices that are zero or negative)
        if 'mid_price' in df.columns:
            invalid_prices = (df['mid_price'] <= 0).sum()
            if invalid_prices > 0:
                logger.warning(f"Found {invalid_prices} invalid prices for {epic}")
                df = df[df['mid_price'] > 0]
        
        final_count = len(df)
        if final_count < initial_count:
            logger.info(f"Data cleaning: {initial_count} -> {final_count} records for {epic}")
        
        return df
    
    def _save_to_database(
        self,
        df: pd.DataFrame,
        epic: str,
        resolution: str,
        instrument: Dict
    ):
        """
        Save data to database
        
        Args:
            df: DataFrame with price data
            epic: EPIC code
            resolution: Time resolution
            instrument: Instrument metadata
        """
        try:
            # Insert price data
            inserted = self.db.insert_prices(df, epic, resolution)
            
            # Update metadata
            metadata = {
                'symbol': instrument.get('symbol', ''),
                'name': instrument.get('name', epic),
                'instrument_type': instrument.get('type', ''),
                'currency': instrument.get('currency', 'USD'),
                'lot_size': instrument.get('lotSize', 1.0),
                'streaming_prices_available': 1 if instrument.get('streamingPricesAvailable') else 0,
                'last_fetch_date': datetime.now(),
                'total_records': self.db.get_data_count(epic)
            }
            self.db.update_metadata(epic, metadata)
            
            logger.info(f"Successfully saved {inserted} records to database for {epic}")
            
        except Exception as e:
            logger.error(f"Error saving to database for {epic}: {e}")
            raise
    
    def _save_to_csv(
        self,
        df: pd.DataFrame,
        epic: str,
        start_date: datetime,
        end_date: datetime,
        resolution: str
    ):
        """
        Save data to CSV file
        
        Args:
            df: DataFrame to save
            epic: EPIC code
            start_date: Start date
            end_date: End date
            resolution: Time resolution
        """
        filename = f"{epic}_{start_date.date()}_{end_date.date()}_{resolution}.csv"
        filepath = self.data_dir / filename
        
        df.to_csv(filepath)
        logger.info(f"Data saved to {filepath}")
        
        # Also save a "latest" version
        latest_filename = f"{epic}_latest_{resolution}.csv"
        latest_filepath = self.data_dir / latest_filename
        df.to_csv(latest_filepath)
        logger.info(f"Latest data saved to {latest_filepath}")
    
    def collect_all_commodities(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        resolution: str = 'HOUR'
    ) -> Dict[str, pd.DataFrame]:
        """
        Collect data for all configured commodities
        
        Args:
            start_date: Start date for collection
            end_date: End date for collection
            resolution: Time resolution
        
        Returns:
            Dictionary with EPIC names as keys and DataFrames as values
        """
        results = {}
        
        for name, epic in COMMODITY_EPICS.items():
            try:
                logger.info(f"Collecting data for {name} ({epic})")
                df = self.collect_historical_data(
                    epic=epic,
                    start_date=start_date,
                    end_date=end_date,
                    resolution=resolution,
                    save_to_file=True,
                    save_to_db=True
                )
                results[name] = df
                
                # Add delay between different commodities
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting data for {name} ({epic}): {e}")
                results[name] = None
        
        return results
    
    def update_daily(self, resolution: str = 'HOUR') -> Dict[str, pd.DataFrame]:
        """
        Update all commodities with latest data (since last update)
        
        Args:
            resolution: Time resolution
        
        Returns:
            Dictionary with update results
        """
        results = {}
        
        for name, epic in COMMODITY_EPICS.items():
            try:
                # Get last date in database
                last_date = self.db.get_latest_date(epic)
                
                if last_date:
                    # Start from day after last update
                    start_date = last_date + timedelta(hours=1)
                else:
                    # No data yet, get last 7 days
                    start_date = datetime.now() - timedelta(days=7)
                
                end_date = datetime.now()
                
                # Skip if already up to date
                if start_date >= end_date:
                    logger.info(f"{name} ({epic}) is already up to date")
                    results[name] = pd.DataFrame()
                    continue
                
                logger.info(f"Updating {name} ({epic}) from {start_date.date()}")
                
                df = self.collect_historical_data(
                    epic=epic,
                    start_date=start_date,
                    end_date=end_date,
                    resolution=resolution,
                    save_to_file=False,
                    save_to_db=True
                )
                results[name] = df
                
                # Add delay between commodities
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error updating {name} ({epic}): {e}")
                results[name] = None
        
        return results
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """
        Get summary statistics of collected data
        
        Args:
            df: DataFrame with price data
        
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {}
        
        summary = {
            'start_date': df.index.min().strftime('%Y-%m-%d %H:%M:%S'),
            'end_date': df.index.max().strftime('%Y-%m-%d %H:%M:%S'),
            'total_records': len(df),
        }
        
        if 'mid_price' in df.columns:
            summary.update({
                'mean_price': df['mid_price'].mean(),
                'min_price': df['mid_price'].min(),
                'max_price': df['mid_price'].max(),
                'std_price': df['mid_price'].std(),
            })
        
        return summary
