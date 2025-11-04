#!/usr/bin/env python3
"""
CLI script to collect historical commodity price data from Capital.com
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta

from src.commodity_collector import CommodityDataCollector
from src.config import COMMODITY_EPICS, CAPITAL_MAX_HISTORICAL_DAYS, LOG_DIR


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIR / 'commodity_collection.log')
        ]
    )


def main():
    parser = argparse.ArgumentParser(
        description='Collect historical commodity price data from Capital.com API'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        help='Start date for data collection (YYYY-MM-DD). Default: 2 years ago'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='End date for data collection (YYYY-MM-DD). Default: now'
    )
    
    parser.add_argument(
        '--commodity',
        type=str,
        choices=list(COMMODITY_EPICS.keys()) + ['all'],
        default='all',
        help='Commodity to collect. Use "all" to collect all commodities.'
    )
    
    parser.add_argument(
        '--resolution',
        type=str,
        choices=['MINUTE', 'HOUR', 'DAY', 'WEEK'],
        default='HOUR',
        help='Time resolution for price data. Default: HOUR'
    )
    
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='Database connection URL (default: SQLite in data directory)'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='Update mode: only fetch new data since last update'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Set dates
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    else:
        # Default to maximum historical range (2 years)
        start_date = end_date - timedelta(days=CAPITAL_MAX_HISTORICAL_DAYS)
    
    logger.info("=" * 60)
    logger.info("Commodity Data Collection Tool")
    logger.info("=" * 60)
    
    if args.update:
        logger.info("Mode: UPDATE (incremental)")
    else:
        logger.info(f"Start date: {start_date.date()}")
        logger.info(f"End date: {end_date.date()}")
        logger.info(f"Commodity: {args.commodity}")
        logger.info(f"Resolution: {args.resolution}")
    
    logger.info("=" * 60)
    
    # Initialize collector
    collector = CommodityDataCollector(database_url=args.database_url)
    
    try:
        if args.update:
            # Update mode: fetch only new data
            logger.info("Fetching updates for all commodities...")
            results = collector.update_daily(resolution=args.resolution)
            
            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("Update Summary")
            logger.info("=" * 60)
            
            for commodity_name, df in results.items():
                if df is not None and not df.empty:
                    summary = collector.get_data_summary(df)
                    logger.info(f"\n{commodity_name}:")
                    logger.info(f"  New records: {summary['total_records']}")
                    if summary.get('mean_price'):
                        logger.info(f"  Mean price: {summary['mean_price']:.4f}")
                elif df is not None:
                    logger.info(f"\n{commodity_name}: Up to date")
                else:
                    logger.warning(f"\n{commodity_name}: Update failed")
        
        elif args.commodity == 'all':
            # Collect all commodities
            logger.info("Collecting data for all commodities...")
            results = collector.collect_all_commodities(
                start_date=start_date,
                end_date=end_date,
                resolution=args.resolution
            )
            
            # Print summary for each commodity
            logger.info("\n" + "=" * 60)
            logger.info("Collection Summary")
            logger.info("=" * 60)
            
            for commodity_name, df in results.items():
                if df is not None and not df.empty:
                    summary = collector.get_data_summary(df)
                    logger.info(f"\n{commodity_name}:")
                    logger.info(f"  Records: {summary['total_records']}")
                    logger.info(f"  Date range: {summary['start_date']} to {summary['end_date']}")
                    if summary.get('mean_price'):
                        logger.info(f"  Mean price: {summary['mean_price']:.4f}")
                        logger.info(f"  Min price: {summary['min_price']:.4f}")
                        logger.info(f"  Max price: {summary['max_price']:.4f}")
                else:
                    logger.warning(f"\n{commodity_name}: No data collected")
        
        else:
            # Collect single commodity
            epic = COMMODITY_EPICS[args.commodity]
            logger.info(f"Collecting data for {args.commodity} ({epic})...")
            
            df = collector.collect_historical_data(
                epic=epic,
                start_date=start_date,
                end_date=end_date,
                resolution=args.resolution,
                save_to_file=True,
                save_to_db=True
            )
            
            if not df.empty:
                summary = collector.get_data_summary(df)
                logger.info("\n" + "=" * 60)
                logger.info("Collection Summary")
                logger.info("=" * 60)
                logger.info(f"Records: {summary['total_records']}")
                logger.info(f"Date range: {summary['start_date']} to {summary['end_date']}")
                if summary.get('mean_price'):
                    logger.info(f"Mean price: {summary['mean_price']:.4f}")
                    logger.info(f"Min price: {summary['min_price']:.4f}")
                    logger.info(f"Max price: {summary['max_price']:.4f}")
            else:
                logger.warning("No data collected")
        
        logger.info("\n" + "=" * 60)
        logger.info("Data collection completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during data collection: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
