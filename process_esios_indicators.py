#!/usr/bin/env python3
"""
Main script for processing ESIOS indicators and collecting data

This script:
1. Parses the indicators file
2. Categorizes indicators for PVPC prediction
3. Sets up PostgreSQL database
4. Downloads indicator data with resume capability
5. Validates data quality
6. Can be scheduled for daily updates

Usage:
    # Generate catalog only
    python process_esios_indicators.py --catalog-only
    
    # Download data for priority 1-2 indicators
    python process_esios_indicators.py --start-date 2024-01-01 --priority 2
    
    # Daily update (gets yesterday's data)
    python process_esios_indicators.py --daily-update
    
    # Resume interrupted download
    python process_esios_indicators.py --start-date 2024-01-01 --resume
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.esios_data_collector import ESIOSDataCollector
from src.database import DatabaseManager
from src.config import ESIOS_API_TOKEN, BASE_DIR, DEFAULT_TIMEZONE


def setup_logging(verbose: bool = False, log_file: Path = None):
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    if log_file:
        root_logger.addHandler(file_handler)
    
    return root_logger


def main():
    parser = argparse.ArgumentParser(
        description='Process ESIOS indicators and collect data for PVPC prediction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate catalog of indicators
  %(prog)s --catalog-only
  
  # Download high-priority data
  %(prog)s --start-date 2024-01-01 --end-date 2024-12-31 --priority 2
  
  # Daily update (yesterday's data)
  %(prog)s --daily-update
  
  # Resume interrupted download
  %(prog)s --start-date 2024-01-01 --resume
        """
    )
    
    # Input/Output
    parser.add_argument(
        '--indicators-file',
        type=Path,
        default=BASE_DIR / 'indicadores_esios_2025-11-03_20-06.txt',
        help='Path to indicators JSON file'
    )
    parser.add_argument(
        '--output-catalog',
        type=Path,
        default=BASE_DIR / 'indicators-pack1.json',
        help='Output path for indicators catalog'
    )
    
    # Database
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='PostgreSQL connection URL (default: from env or localhost)'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database schema'
    )
    
    # Data collection
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for data collection (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for data collection (YYYY-MM-DD). Default: yesterday'
    )
    parser.add_argument(
        '--priority',
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5],
        help='Maximum priority level to collect (1=highest, 5=lowest)'
    )
    parser.add_argument(
        '--daily-update',
        action='store_true',
        help='Update with yesterday\'s data only'
    )
    
    # Execution control
    parser.add_argument(
        '--catalog-only',
        action='store_true',
        help='Only generate the indicators catalog, no data download'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )
    parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force re-download of existing data'
    )
    
    # API
    parser.add_argument(
        '--api-token',
        type=str,
        default=None,
        help='ESIOS API token (default: from .env)'
    )
    
    # Logging
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        default=None,
        help='Log file path (default: logs/esios_TIMESTAMP.log)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.log_file is None:
        log_dir = BASE_DIR / 'logs'
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.log_file = log_dir / f'esios_{timestamp}.log'
    
    logger = setup_logging(args.verbose, args.log_file)
    logger.info("="*80)
    logger.info("ESIOS Data Collection Script")
    logger.info("="*80)
    logger.info(f"Log file: {args.log_file}")
    
    try:
        # Initialize collector
        api_token = args.api_token or ESIOS_API_TOKEN
        if not api_token:
            logger.error("No API token provided. Set ESIOS_API_TOKEN in .env or use --api-token")
            sys.exit(1)
        
        collector = ESIOSDataCollector(
            api_token=api_token,
            database_url=args.database_url
        )
        
        # Initialize database if requested
        if args.init_db:
            logger.info("Initializing database schema...")
            collector.db.create_tables()
            logger.info("Database initialized successfully")
        
        # Check if indicators file exists
        if not args.indicators_file.exists():
            logger.error(f"Indicators file not found: {args.indicators_file}")
            sys.exit(1)
        
        # Step 1: Generate indicators catalog
        logger.info("-"*80)
        logger.info("Step 1: Generating indicators catalog")
        logger.info("-"*80)
        
        indicators = collector.generate_indicators_catalog(
            args.indicators_file,
            args.output_catalog
        )
        
        logger.info(f"Catalog generated: {args.output_catalog}")
        logger.info(f"Total indicators: {len(indicators)}")
        
        # Show category breakdown
        categories = {}
        for ind in indicators:
            cat = ind['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info("\nIndicators by category:")
        for cat, count in sorted(categories.items()):
            logger.info(f"  {cat:15s}: {count:4d}")
        
        logger.info("\nIndicators by priority:")
        priorities = {}
        for ind in indicators:
            pri = ind['priority']
            priorities[pri] = priorities.get(pri, 0) + 1
        
        for pri in sorted(priorities.keys()):
            logger.info(f"  Priority {pri}: {priorities[pri]:4d}")
        
        # Stop here if catalog-only
        if args.catalog_only:
            logger.info("\n" + "="*80)
            logger.info("Catalog generation completed. Exiting (--catalog-only)")
            logger.info("="*80)
            logger.info(f"\nOutput: {args.output_catalog}")
            logger.info(f"Log: {args.log_file}")
            return
        
        # Save indicators metadata to database
        logger.info("\nSaving indicators metadata to database...")
        collector.db.bulk_insert_indicators(indicators)
        logger.info("Metadata saved successfully")
        
        # Step 2: Collect data
        logger.info("\n" + "-"*80)
        logger.info("Step 2: Collecting indicator data")
        logger.info("-"*80)
        
        # Determine date range
        tz = pytz.timezone(DEFAULT_TIMEZONE)
        now = datetime.now(tz)
        
        if args.daily_update:
            # Get yesterday's data
            yesterday = now - timedelta(days=1)
            start_date = yesterday.strftime('%Y-%m-%d')
            end_date = yesterday.strftime('%Y-%m-%d')
            logger.info(f"Daily update mode: collecting data for {start_date}")
        else:
            if not args.start_date:
                logger.error("--start-date is required (or use --daily-update)")
                sys.exit(1)
            
            start_date = args.start_date
            end_date = args.end_date or (now - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Priority filter: <= {args.priority}")
        logger.info(f"Resume enabled: {args.resume}")
        
        # Collect data
        collector.collect_all_indicators(
            indicators=indicators,
            start_date=start_date,
            end_date=end_date,
            max_priority=args.priority,
            resume=args.resume
        )
        
        # Step 3: Validate data quality
        logger.info("\n" + "-"*80)
        logger.info("Step 3: Data quality validation")
        logger.info("-"*80)
        
        priority_indicators = [ind for ind in indicators if ind['priority'] <= args.priority]
        
        for ind in priority_indicators[:10]:  # Sample first 10
            indicator_id = ind['id']
            quality = collector.db.validate_data_quality(
                indicator_id,
                start_date,
                end_date
            )
            
            logger.info(f"\nIndicator {indicator_id} ({ind['short_name']}):")
            logger.info(f"  Records: {quality['record_count']}")
            logger.info(f"  Completeness: {quality['completeness']*100:.1f}%")
            if quality['avg_value']:
                logger.info(f"  Avg value: {quality['avg_value']:.2f}")
        
        logger.info("\n" + "="*80)
        logger.info("Data collection completed successfully!")
        logger.info("="*80)
        logger.info(f"\nLog file: {args.log_file}")
        logger.info(f"Catalog: {args.output_catalog}")
        logger.info("\nNext steps:")
        logger.info("1. Review the log file for any errors")
        logger.info("2. Check indicators-pack1.json for categorized indicators")
        logger.info("3. Query the database to analyze collected data")
        logger.info("4. Set up daily cron job for automatic updates:")
        logger.info(f"   0 1 * * * {sys.executable} {Path(__file__).absolute()} --daily-update")
        
    except KeyboardInterrupt:
        logger.warning("\n\nInterrupted by user. Progress saved to checkpoint.")
        logger.info("Resume with: python process_esios_indicators.py --resume")
        sys.exit(130)
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
