#!/usr/bin/env python3
"""
CLI script to collect historical PVPC data
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta

from src.data_collector import PVPCDataCollector
from src.config import DEFAULT_START_DATE, INDICATORS


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/data_collection.log')
        ]
    )


def main():
    parser = argparse.ArgumentParser(
        description='Collect historical PVPC electricity price data from ESIOS API'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=DEFAULT_START_DATE,
        help=f'Start date for data collection (YYYY-MM-DD). Default: {DEFAULT_START_DATE}'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='End date for data collection (YYYY-MM-DD). Default: yesterday'
    )
    
    parser.add_argument(
        '--indicator',
        type=str,
        choices=list(INDICATORS.keys()) + ['all'],
        default='pvpc_2.0TD',
        help='Indicator to collect. Use "all" to collect all indicators.'
    )
    
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='ESIOS API token (can also be set via ESIOS_API_TOKEN env var)'
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
    
    # Set end date if not provided
    if args.end_date is None:
        args.end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    logger.info("=" * 60)
    logger.info("PVPC Data Collection Tool")
    logger.info("=" * 60)
    logger.info(f"Start date: {args.start_date}")
    logger.info(f"End date: {args.end_date}")
    logger.info(f"Indicator: {args.indicator}")
    logger.info("=" * 60)
    
    # Initialize collector
    collector = PVPCDataCollector(api_token=args.token)
    
    try:
        if args.indicator == 'all':
            # Collect all indicators
            logger.info("Collecting data for all indicators...")
            results = collector.collect_all_indicators(
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            # Print summary for each indicator
            logger.info("\n" + "=" * 60)
            logger.info("Collection Summary")
            logger.info("=" * 60)
            
            for indicator_name, df in results.items():
                if df is not None and not df.empty:
                    summary = collector.get_data_summary(df)
                    logger.info(f"\n{indicator_name}:")
                    logger.info(f"  Records: {summary['total_records']}")
                    logger.info(f"  Date range: {summary['start_date']} to {summary['end_date']}")
                    if summary['mean_price']:
                        logger.info(f"  Mean price: {summary['mean_price']:.2f} EUR/MWh")
                        logger.info(f"  Min price: {summary['min_price']:.2f} EUR/MWh")
                        logger.info(f"  Max price: {summary['max_price']:.2f} EUR/MWh")
                else:
                    logger.warning(f"\n{indicator_name}: No data collected")
        else:
            # Collect single indicator
            logger.info(f"Collecting data for {args.indicator}...")
            df = collector.collect_historical_data(
                start_date=args.start_date,
                end_date=args.end_date,
                indicator_name=args.indicator,
                save_to_file=True
            )
            
            if not df.empty:
                summary = collector.get_data_summary(df)
                logger.info("\n" + "=" * 60)
                logger.info("Collection Summary")
                logger.info("=" * 60)
                logger.info(f"Records: {summary['total_records']}")
                logger.info(f"Date range: {summary['start_date']} to {summary['end_date']}")
                if summary['mean_price']:
                    logger.info(f"Mean price: {summary['mean_price']:.2f} EUR/MWh")
                    logger.info(f"Min price: {summary['min_price']:.2f} EUR/MWh")
                    logger.info(f"Max price: {summary['max_price']:.2f} EUR/MWh")
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
