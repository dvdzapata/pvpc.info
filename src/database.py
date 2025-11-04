"""
Database models and setup for ESIOS data storage
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

Base = declarative_base()


class Indicator(Base):
    """ESIOS Indicator metadata"""
    __tablename__ = 'indicators'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    short_name = Column(String(200))
    description = Column(Text)
    category = Column(String(100))  # Assigned category (price, production, demand, etc.)
    priority = Column(Integer, default=5)  # 1=highest, 5=lowest
    is_active = Column(Boolean, default=True)  # Whether to actively collect this indicator
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_indicator_category', 'category'),
        Index('idx_indicator_active', 'is_active'),
    )


class IndicatorValue(Base):
    """Time-series values for indicators"""
    __tablename__ = 'indicator_values'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_id = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    value_min = Column(Float)  # Some indicators have min/max ranges
    value_max = Column(Float)
    geo_id = Column(Integer)  # For geographic data (provinces, etc.)
    geo_name = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_indicator_datetime', 'indicator_id', 'datetime'),
        Index('idx_datetime', 'datetime'),
        Index('idx_indicator_id', 'indicator_id'),
    )


class DataCollectionLog(Base):
    """Log of data collection operations"""
    __tablename__ = 'data_collection_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_id = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    records_fetched = Column(Integer, default=0)
    status = Column(String(50))  # success, failed, partial
    error_message = Column(Text)
    execution_time_seconds = Column(Float)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_log_indicator', 'indicator_id'),
        Index('idx_log_status', 'status'),
        Index('idx_log_created', 'created_at'),
    )


class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager
        
        Args:
            database_url: PostgreSQL connection URL
        """
        if database_url is None:
            # Default to environment variable or local PostgreSQL
            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql://postgres:postgres@localhost:5432/esios_data'
            )
        
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables in the database"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(self.engine)
        logger.info("Database tables dropped")
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def bulk_insert_indicators(self, indicators_data: list):
        """
        Bulk insert indicator metadata
        
        Args:
            indicators_data: List of indicator dictionaries
        """
        session = self.get_session()
        try:
            for ind_data in indicators_data:
                # Check if indicator exists
                existing = session.query(Indicator).filter_by(id=ind_data['id']).first()
                if existing:
                    # Update existing
                    for key, value in ind_data.items():
                        if key != 'id' and hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # Insert new
                    indicator = Indicator(**ind_data)
                    session.add(indicator)
            
            session.commit()
            logger.info(f"Successfully inserted/updated {len(indicators_data)} indicators")
        except Exception as e:
            session.rollback()
            logger.error(f"Error bulk inserting indicators: {e}")
            raise
        finally:
            session.close()
    
    def bulk_insert_values(self, values_data: list, batch_size: int = 10000):
        """
        Bulk insert indicator values
        
        Args:
            values_data: List of value dictionaries
            batch_size: Number of records per batch
        """
        session = self.get_session()
        try:
            for i in range(0, len(values_data), batch_size):
                batch = values_data[i:i + batch_size]
                
                # Convert to IndicatorValue objects
                objects = [IndicatorValue(**val) for val in batch]
                session.bulk_save_objects(objects)
                session.commit()
                
                logger.info(f"Inserted batch {i // batch_size + 1}: {len(batch)} records")
            
            logger.info(f"Successfully inserted {len(values_data)} values")
        except Exception as e:
            session.rollback()
            logger.error(f"Error bulk inserting values: {e}")
            raise
        finally:
            session.close()
    
    def get_latest_data_date(self, indicator_id: int):
        """
        Get the latest date for which we have data for an indicator
        
        Args:
            indicator_id: ID of the indicator
            
        Returns:
            datetime or None
        """
        session = self.get_session()
        try:
            result = session.query(IndicatorValue.datetime)\
                .filter_by(indicator_id=indicator_id)\
                .order_by(IndicatorValue.datetime.desc())\
                .first()
            return result[0] if result else None
        finally:
            session.close()
    
    def log_collection(self, log_data: dict):
        """
        Log a data collection operation
        
        Args:
            log_data: Dictionary with log information
        """
        session = self.get_session()
        try:
            log = DataCollectionLog(**log_data)
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging collection: {e}")
        finally:
            session.close()
    
    def get_active_indicators(self):
        """Get list of active indicators"""
        session = self.get_session()
        try:
            indicators = session.query(Indicator).filter_by(is_active=True).all()
            return [{'id': i.id, 'name': i.name, 'category': i.category, 'priority': i.priority} 
                    for i in indicators]
        finally:
            session.close()
    
    def validate_data_quality(self, indicator_id: int, start_date, end_date):
        """
        Validate data quality for an indicator in a date range
        
        Args:
            indicator_id: ID of the indicator
            start_date: Start date
            end_date: End date
            
        Returns:
            dict with quality metrics
        """
        session = self.get_session()
        try:
            # Count records
            count = session.query(IndicatorValue)\
                .filter(
                    IndicatorValue.indicator_id == indicator_id,
                    IndicatorValue.datetime >= start_date,
                    IndicatorValue.datetime <= end_date
                ).count()
            
            # Check for nulls
            null_count = session.query(IndicatorValue)\
                .filter(
                    IndicatorValue.indicator_id == indicator_id,
                    IndicatorValue.datetime >= start_date,
                    IndicatorValue.datetime <= end_date,
                    IndicatorValue.value.is_(None)
                ).count()
            
            # Get value statistics
            from sqlalchemy import func
            stats = session.query(
                func.min(IndicatorValue.value),
                func.max(IndicatorValue.value),
                func.avg(IndicatorValue.value)
            ).filter(
                IndicatorValue.indicator_id == indicator_id,
                IndicatorValue.datetime >= start_date,
                IndicatorValue.datetime <= end_date
            ).first()
            
            return {
                'record_count': count,
                'null_count': null_count,
                'min_value': stats[0] if stats else None,
                'max_value': stats[1] if stats else None,
                'avg_value': stats[2] if stats else None,
                'completeness': (count - null_count) / count if count > 0 else 0
            }
        finally:
            session.close()
