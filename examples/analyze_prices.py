#!/usr/bin/env python3
"""
Example script showing basic analysis of PVPC data

This script demonstrates how to:
- Load collected PVPC data
- Perform basic statistical analysis
- Identify price patterns
- Create simple visualizations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


def load_data(filepath='data/pvpc_2.0TD_latest.csv'):
    """Load PVPC data from CSV file"""
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath, index_col='datetime', parse_dates=True)
    print(f"Loaded {len(df)} records")
    return df


def basic_statistics(df):
    """Calculate and display basic statistics"""
    print("\n" + "="*60)
    print("BASIC STATISTICS")
    print("="*60)
    
    price_col = 'price_eur_mwh' if 'price_eur_mwh' in df.columns else 'value'
    
    print(f"\nDate range: {df.index.min()} to {df.index.max()}")
    print(f"Total hours: {len(df)}")
    print(f"\nPrice Statistics (EUR/MWh):")
    print(f"  Mean:   {df[price_col].mean():.2f}")
    print(f"  Median: {df[price_col].median():.2f}")
    print(f"  Min:    {df[price_col].min():.2f}")
    print(f"  Max:    {df[price_col].max():.2f}")
    print(f"  Std:    {df[price_col].std():.2f}")
    
    return price_col


def hourly_pattern(df, price_col):
    """Analyze price patterns by hour of day"""
    print("\n" + "="*60)
    print("HOURLY PATTERN")
    print("="*60)
    
    hourly = df.groupby(df.index.hour)[price_col].agg(['mean', 'min', 'max'])
    
    print("\nAverage price by hour of day:")
    print("Hour | Mean (EUR/MWh) | Min (EUR/MWh) | Max (EUR/MWh)")
    print("-" * 60)
    for hour, row in hourly.iterrows():
        print(f"{hour:02d}h  | {row['mean']:13.2f} | {row['min']:13.2f} | {row['max']:13.2f}")
    
    # Find cheapest and most expensive hours
    cheapest_hour = hourly['mean'].idxmin()
    expensive_hour = hourly['mean'].idxmax()
    
    print(f"\n💡 Cheapest hour: {cheapest_hour:02d}:00 ({hourly.loc[cheapest_hour, 'mean']:.2f} EUR/MWh)")
    print(f"💰 Most expensive hour: {expensive_hour:02d}:00 ({hourly.loc[expensive_hour, 'mean']:.2f} EUR/MWh)")
    
    return hourly


def daily_pattern(df, price_col):
    """Analyze price patterns by day of week"""
    print("\n" + "="*60)
    print("DAILY PATTERN")
    print("="*60)
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily = df.groupby(df.index.dayofweek)[price_col].agg(['mean', 'min', 'max'])
    
    print("\nAverage price by day of week:")
    print("Day       | Mean (EUR/MWh) | Min (EUR/MWh) | Max (EUR/MWh)")
    print("-" * 60)
    for day_idx, row in daily.iterrows():
        print(f"{days[day_idx]:9} | {row['mean']:13.2f} | {row['min']:13.2f} | {row['max']:13.2f}")
    
    return daily


def monthly_trend(df, price_col):
    """Analyze monthly price trends"""
    print("\n" + "="*60)
    print("MONTHLY TREND")
    print("="*60)
    
    monthly = df.groupby(df.index.to_period('M'))[price_col].agg(['mean', 'min', 'max'])
    
    print("\nAverage price by month:")
    print("Month    | Mean (EUR/MWh) | Min (EUR/MWh) | Max (EUR/MWh)")
    print("-" * 60)
    for month, row in monthly.tail(12).iterrows():
        print(f"{str(month):8} | {row['mean']:13.2f} | {row['min']:13.2f} | {row['max']:13.2f}")
    
    return monthly


def price_distribution(df, price_col):
    """Analyze price distribution"""
    print("\n" + "="*60)
    print("PRICE DISTRIBUTION")
    print("="*60)
    
    # Calculate percentiles
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    print("\nPrice percentiles (EUR/MWh):")
    for p in percentiles:
        value = df[price_col].quantile(p/100)
        print(f"  P{p:2d}: {value:6.2f}")
    
    # Count extreme prices
    mean = df[price_col].mean()
    std = df[price_col].std()
    
    low_prices = (df[price_col] < mean - 2*std).sum()
    high_prices = (df[price_col] > mean + 2*std).sum()
    
    print(f"\nExtreme prices (> 2σ from mean):")
    print(f"  Very low prices: {low_prices} hours ({100*low_prices/len(df):.1f}%)")
    print(f"  Very high prices: {high_prices} hours ({100*high_prices/len(df):.1f}%)")


def create_visualizations(df, price_col, hourly, output_dir='examples'):
    """Create visualization plots"""
    print("\n" + "="*60)
    print("CREATING VISUALIZATIONS")
    print("="*60)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 1. Time series plot (last 30 days)
    plt.figure(figsize=(14, 6))
    recent = df.tail(30*24)  # Last 30 days
    plt.plot(recent.index, recent[price_col], linewidth=0.5)
    plt.title('PVPC Price - Last 30 Days', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Price (EUR/MWh)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = output_path / 'price_timeseries.png'
    plt.savefig(filepath, dpi=150)
    print(f"✓ Saved time series plot: {filepath}")
    plt.close()
    
    # 2. Hourly pattern bar chart
    plt.figure(figsize=(12, 6))
    hourly['mean'].plot(kind='bar', color='steelblue')
    plt.title('Average PVPC Price by Hour of Day', fontsize=14, fontweight='bold')
    plt.xlabel('Hour')
    plt.ylabel('Average Price (EUR/MWh)')
    plt.grid(True, alpha=0.3, axis='y')
    plt.xticks(range(24), [f'{h:02d}h' for h in range(24)], rotation=0)
    plt.tight_layout()
    filepath = output_path / 'hourly_pattern.png'
    plt.savefig(filepath, dpi=150)
    print(f"✓ Saved hourly pattern plot: {filepath}")
    plt.close()
    
    # 3. Price distribution histogram
    plt.figure(figsize=(10, 6))
    plt.hist(df[price_col], bins=50, color='lightblue', edgecolor='black', alpha=0.7)
    plt.axvline(df[price_col].mean(), color='red', linestyle='--', 
                linewidth=2, label=f'Mean: {df[price_col].mean():.2f}')
    plt.axvline(df[price_col].median(), color='green', linestyle='--', 
                linewidth=2, label=f'Median: {df[price_col].median():.2f}')
    plt.title('PVPC Price Distribution', fontsize=14, fontweight='bold')
    plt.xlabel('Price (EUR/MWh)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    filepath = output_path / 'price_distribution.png'
    plt.savefig(filepath, dpi=150)
    print(f"✓ Saved distribution plot: {filepath}")
    plt.close()
    
    # 4. Heatmap of prices by hour and day
    plt.figure(figsize=(14, 8))
    pivot = df.copy()
    pivot['hour'] = pivot.index.hour
    pivot['day'] = pivot.index.date
    pivot_table = pivot.pivot_table(values=price_col, index='hour', columns='day', aggfunc='mean')
    
    # Only show last 30 days for readability
    pivot_table = pivot_table.iloc[:, -30:]
    
    plt.imshow(pivot_table, aspect='auto', cmap='RdYlGn_r', interpolation='nearest')
    plt.colorbar(label='Price (EUR/MWh)')
    plt.title('PVPC Price Heatmap - Last 30 Days', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Hour of Day')
    plt.yticks(range(24), [f'{h:02d}h' for h in range(24)])
    
    # Show only some date labels to avoid overcrowding
    date_labels = [str(d)[-5:] for d in pivot_table.columns[::5]]
    plt.xticks(range(0, len(pivot_table.columns), 5), date_labels, rotation=45)
    
    plt.tight_layout()
    filepath = output_path / 'price_heatmap.png'
    plt.savefig(filepath, dpi=150)
    print(f"✓ Saved heatmap plot: {filepath}")
    plt.close()


def savings_calculator(hourly, monthly_consumption_kwh=250):
    """Calculate potential savings by shifting consumption to cheaper hours"""
    print("\n" + "="*60)
    print("SAVINGS CALCULATOR")
    print("="*60)
    
    print(f"\nAssuming monthly consumption: {monthly_consumption_kwh} kWh")
    
    # Convert EUR/MWh to EUR/kWh
    mean_price_kwh = hourly['mean'].mean() / 1000
    cheapest_price_kwh = hourly['mean'].min() / 1000
    
    # Calculate costs
    avg_monthly_cost = monthly_consumption_kwh * mean_price_kwh
    optimal_monthly_cost = monthly_consumption_kwh * cheapest_price_kwh
    potential_savings = avg_monthly_cost - optimal_monthly_cost
    
    print(f"\nAverage hourly price: {mean_price_kwh*1000:.2f} EUR/MWh = {mean_price_kwh:.4f} EUR/kWh")
    print(f"Cheapest hour price: {cheapest_price_kwh*1000:.2f} EUR/MWh = {cheapest_price_kwh:.4f} EUR/kWh")
    print(f"\nMonthly cost at average price: {avg_monthly_cost:.2f} EUR")
    print(f"Monthly cost at cheapest hour: {optimal_monthly_cost:.2f} EUR")
    print(f"Potential monthly savings: {potential_savings:.2f} EUR ({100*potential_savings/avg_monthly_cost:.1f}%)")
    print(f"Potential annual savings: {potential_savings*12:.2f} EUR")


def main():
    """Main analysis function"""
    try:
        # Load data
        df = load_data()
        
        if df.empty:
            print("\n❌ No data found. Please run data collection first:")
            print("   python collect_data.py --start-date 2024-01-01")
            return
        
        # Perform analysis
        price_col = basic_statistics(df)
        hourly = hourly_pattern(df, price_col)
        daily_pattern(df, price_col)
        monthly_trend(df, price_col)
        price_distribution(df, price_col)
        
        # Create visualizations
        try:
            create_visualizations(df, price_col, hourly)
        except Exception as e:
            print(f"\n⚠️  Could not create visualizations: {e}")
            print("   (matplotlib may not be properly configured)")
        
        # Calculate savings
        savings_calculator(hourly)
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE!")
        print("="*60)
        print("\n💡 Tips for saving on electricity:")
        print("  1. Use appliances during off-peak hours (typically 2-7 AM)")
        print("  2. Avoid peak hours (typically 7-10 PM)")
        print("  3. Monitor daily prices to adjust consumption")
        print("  4. Consider time-of-use strategies for EV charging and heating")
        
    except FileNotFoundError:
        print("\n❌ Data file not found!")
        print("Please collect data first:")
        print("  python collect_data.py --start-date 2024-01-01")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
