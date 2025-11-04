"""
Database models and utilities for storing commodity price data
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Index, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import logging
import os

from .config import BASE_DIR

logger = logging.getLogger(__name__)

Base = declarative_base()


def _get_utcnow():
    """Helper function to get current UTC time"""
    return datetime.utcnow()


class CommodityPrice(Base):
    """Model for commodity price data"""
    __tablename__ = 'commodity_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    epic = Column(String(50), nullable=False, index=True)
    datetime = Column(DateTime, nullable=False, index=True)
    
    # Price data
    bid = Column(Float)
    ask = Column(Float)
    mid_price = Column(Float)
    open_price_bid = Column(Float)
    open_price_ask = Column(Float)
    high_price_bid = Column(Float)
    high_price_ask = Column(Float)
    low_price_bid = Column(Float)
    low_price_ask = Column(Float)
    
    # Volume
    last_traded_volume = Column(Integer)
    
    # Metadata
    instrument_type = Column(String(50))
    instrument_name = Column(String(100))
    resolution = Column(String(20))  # MINUTE, HOUR, DAY, WEEK
    
    # Timestamps
    created_at = Column(DateTime, default=_get_utcnow)
    updated_at = Column(DateTime, default=_get_utcnow, onupdate=_get_utcnow)
    
    # Composite index for efficient querying
    __table_args__ = (
        Index('idx_epic_datetime', 'epic', 'datetime'),
    )
    
    def __repr__(self):
        return f"<CommodityPrice(epic='{self.epic}', datetime='{self.datetime}', mid_price={self.mid_price})>"


class CommodityMetadata(Base):
    """Model for commodity metadata"""
    __tablename__ = 'commodity_metadata'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    epic = Column(String(50), nullable=False, unique=True, index=True)
    
    # Instrument information
    symbol = Column(String(50))
    name = Column(String(100))
    instrument_type = Column(String(50))
    currency = Column(String(10))
    lot_size = Column(Float)
    
    # Market information
    market_status = Column(String(20))
    streaming_prices_available = Column(Integer)  # Boolean as int
    
    # Last update tracking
    last_fetch_date = Column(DateTime)
    total_records = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=_get_utcnow)
    updated_at = Column(DateTime, default=_get_utcnow, onupdate=_get_utcnow)
    
    def __repr__(self):
        return f"<CommodityMetadata(epic='{self.epic}', name='{self.name}')>"


class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection URL. If None, uses SQLite in data directory
        """
        if database_url is None:
            db_path = BASE_DIR / 'data' / 'commodities.db'
            database_url = f'sqlite:///{db_path}'
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info(f"Database initialized: {database_url}")
    
    def create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created/verified")
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def insert_prices(self, prices_df, epic: str, resolution: str = 'HOUR'):
        """
        Insert price data into database
        
        Args:
            prices_df: DataFrame with price data
            epic: EPIC code
            resolution: Time resolution
        
        Returns:
            Number of records inserted
        """
        if prices_df.empty:
            logger.warning(f"No data to insert for {epic}")
            return 0
        
        session = self.get_session()
        try:
            inserted_count = 0
            
            for idx, row in prices_df.iterrows():
                # Check if record already exists
                existing = session.query(CommodityPrice).filter_by(
                    epic=epic,
                    datetime=idx
                ).first()
                
                if existing:
                    # Update existing record
                    existing.bid = row.get('bid')
                    existing.ask = row.get('ask')
                    existing.mid_price = row.get('mid_price')
                    existing.last_traded_volume = row.get('lastTradedVolume')
                    existing.instrument_type = row.get('instrument_type', '')
                    existing.resolution = resolution
                    existing.updated_at = datetime.utcnow()
                else:
                    # Insert new record
                    price_record = CommodityPrice(
                        epic=epic,
                        datetime=idx,
                        bid=row.get('bid'),
                        ask=row.get('ask'),
                        mid_price=row.get('mid_price'),
                        last_traded_volume=row.get('lastTradedVolume'),
                        instrument_type=row.get('instrument_type', ''),
                        resolution=resolution
                    )
                    session.add(price_record)
                    inserted_count += 1
            
            session.commit()
            logger.info(f"Inserted/updated {inserted_count} price records for {epic}")
            return inserted_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting prices: {e}")
            raise
        finally:
            session.close()
    
    def update_metadata(self, epic: str, metadata: dict):
        """
        Update commodity metadata
        
        Args:
            epic: EPIC code
            metadata: Dictionary with metadata fields
        """
        session = self.get_session()
        try:
            record = session.query(CommodityMetadata).filter_by(epic=epic).first()
            
            if record:
                # Update existing
                for key, value in metadata.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                record.updated_at = datetime.utcnow()
            else:
                # Create new
                record = CommodityMetadata(epic=epic, **metadata)
                session.add(record)
            
            session.commit()
            logger.info(f"Updated metadata for {epic}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating metadata: {e}")
            raise
        finally:
            session.close()
    
    def get_latest_date(self, epic: str) -> datetime:
        """
        Get the latest date for which we have data for an EPIC
        
        Args:
            epic: EPIC code
        
        Returns:
            Latest datetime or None if no data exists
        """
        session = self.get_session()
        try:
            result = session.query(CommodityPrice.datetime).filter_by(
                epic=epic
            ).order_by(CommodityPrice.datetime.desc()).first()
            
            return result[0] if result else None
        finally:
            session.close()
    
    def get_data_count(self, epic: str) -> int:
        """
        Get count of records for an EPIC
        
        Args:
            epic: EPIC code
        
        Returns:
            Number of records
        """
        session = self.get_session()
        try:
            count = session.query(CommodityPrice).filter_by(epic=epic).count()
            return count
        finally:
            session.close()
