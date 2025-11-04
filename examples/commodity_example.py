#!/usr/bin/env python3
"""
Example script demonstrating commodity data collection usage
"""
from datetime import datetime, timedelta
import pandas as pd
from src.commodity_collector import CommodityDataCollector
from src.database import DatabaseManager

def main():
    print("=" * 60)
    print("Commodity Data Collection Example")
    print("=" * 60)
    
    # Initialize collector
    collector = CommodityDataCollector()
    print("\n✓ Collector initialized")
    
    # Example 1: Collect data for a single commodity
    print("\n1. Collecting crude oil data for last 7 days...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    df = collector.collect_historical_data(
        epic='CRUDE_OIL',
        start_date=start_date,
        end_date=end_date,
        resolution='HOUR',
        save_to_file=True,
        save_to_db=True
    )
    
    if not df.empty:
        print(f"   ✓ Collected {len(df)} records")
        print(f"   Date range: {df.index.min()} to {df.index.max()}")
        if 'mid_price' in df.columns:
            print(f"   Price range: ${df['mid_price'].min():.2f} - ${df['mid_price'].max():.2f}")
    else:
        print("   ⚠ No data collected")
    
    # Example 2: Get data summary
    print("\n2. Getting data summary...")
    summary = collector.get_data_summary(df)
    if summary:
        print(f"   Total records: {summary['total_records']}")
        if summary.get('mean_price'):
            print(f"   Average price: ${summary['mean_price']:.2f}")
            print(f"   Std deviation: ${summary['std_price']:.2f}")
    
    # Example 3: Query data from database
    print("\n3. Querying data from database...")
    db = DatabaseManager()
    
    latest_date = db.get_latest_date('CRUDE_OIL')
    if latest_date:
        print(f"   ✓ Latest data: {latest_date}")
    
    count = db.get_data_count('CRUDE_OIL')
    print(f"   ✓ Total records in DB: {count}")
    
    # Example 4: Show basic statistics
    if not df.empty and 'mid_price' in df.columns:
        print("\n4. Basic statistics:")
        print(df['mid_price'].describe())
        
        # Show first few records
        print("\n5. Sample data:")
        print(df[['bid', 'ask', 'mid_price']].head())
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Check the data directory for CSV files")
    print("  - Check the database: data/commodities.db")
    print("  - Try: python collect_commodities.py --help")
    print("=" * 60)

if __name__ == '__main__':
    main()
