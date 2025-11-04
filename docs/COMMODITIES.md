# Commodity Data Collection from Capital.com

This document describes the commodity price data collection system that retrieves historical and real-time market data from Capital.com API.

## Overview

The system collects historical price data for various commodities including crude oil, natural gas, brent oil, and carbon emissions futures. Data is stored in a SQLite database with CSV backups for analysis.

## Features

- ✅ Historical data collection (up to 2 years)
- ✅ Multiple time resolutions (MINUTE, HOUR, DAY, WEEK)
- ✅ Automatic data validation and quality checks
- ✅ SQLite database storage with automatic schema management
- ✅ CSV export for backup and analysis
- ✅ Daily incremental updates
- ✅ Rate limiting to respect API constraints
- ✅ Comprehensive error handling and logging
- ✅ Support for multiple commodity types

## Supported Commodities

### Real-time CFDs
- **crude_oil_rt**: Crude Oil CFD (Real-time)
- **natural_gas_rt**: Natural Gas CFD (Real-time)
- **brent_oil_rt**: Brent Crude Oil CFD (Real-time)
- **gas_london_rt**: Natural Gas London CFD (Real-time)

### Futures Contracts - Carbon Emissions
- **carbon_dec_2025**: Carbon Emissions December 2025

### Futures Contracts - Natural Gas
- **gas_eu_ttf_dec_2025**: Natural Gas EU TTF December 2025
- **gas_eu_ttf_jan_2026**: Natural Gas EU TTF January 2026
- **gas_eu_ttf_feb_2026**: Natural Gas EU TTF February 2026

### Futures Contracts - Brent Oil
- **brent_oil_jan_2026**: Brent Oil January 2026
- **brent_oil_feb_2026**: Brent Oil February 2026

### Futures Contracts - Crude Oil
- **crude_oil_dec_2025**: Crude Oil December 2025
- **crude_oil_jan_2026**: Crude Oil January 2026

### Futures Contracts - Gas London
- **gas_london_nov_2025**: Gas London November 2025

## Installation

The commodity collection system uses the same dependencies as the main PVPC project:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Collect all commodities with default settings (2 years of hourly data):

```bash
python collect_commodities.py --commodity all
```

### Collect Specific Commodity

Collect data for a specific commodity:

```bash
python collect_commodities.py --commodity crude_oil_rt
```

### Specify Date Range

Collect data for a specific date range:

```bash
python collect_commodities.py --commodity all --start-date 2023-01-01 --end-date 2024-12-31
```

### Different Time Resolutions

Collect data at different time resolutions:

```bash
# Daily prices
python collect_commodities.py --commodity crude_oil_rt --resolution DAY

# Minute-level prices (use with caution - large data volumes)
python collect_commodities.py --commodity crude_oil_rt --resolution MINUTE --start-date 2024-11-01

# Weekly prices
python collect_commodities.py --commodity all --resolution WEEK
```

### Daily Updates

Update all commodities with the latest data (incremental update):

```bash
python collect_commodities.py --update
```

This mode:
- Checks the last date in the database for each commodity
- Only fetches new data since the last update
- Much faster than full historical collection

### Verbose Logging

Enable detailed logging for debugging:

```bash
python collect_commodities.py --commodity all --verbose
```

### Custom Database

Use a custom database URL:

```bash
python collect_commodities.py --database-url postgresql://user:pass@localhost/commodities
```

## Data Storage

### Database Schema

Data is stored in a SQLite database (`data/commodities.db`) with two main tables:

#### commodity_prices
Stores historical price data:
- `id`: Primary key
- `epic`: Commodity EPIC code
- `datetime`: Timestamp of the price
- `bid`: Bid price
- `ask`: Ask price
- `mid_price`: Mid price (average of bid and ask)
- `open_price_bid`, `open_price_ask`: Opening prices
- `high_price_bid`, `high_price_ask`: High prices
- `low_price_bid`, `low_price_ask`: Low prices
- `last_traded_volume`: Trading volume
- `instrument_type`: Type of instrument (e.g., COMMODITIES)
- `instrument_name`: Human-readable name
- `resolution`: Time resolution (MINUTE, HOUR, DAY, WEEK)
- `created_at`, `updated_at`: Timestamps

#### commodity_metadata
Stores commodity metadata:
- `id`: Primary key
- `epic`: Commodity EPIC code (unique)
- `symbol`: Short symbol
- `name`: Full name
- `instrument_type`: Type of instrument
- `currency`: Currency (usually USD)
- `lot_size`: Lot size for trading
- `market_status`: Current market status
- `streaming_prices_available`: Whether streaming prices are available
- `last_fetch_date`: Last time data was fetched
- `total_records`: Total number of price records
- `created_at`, `updated_at`: Timestamps

### CSV Files

Data is also saved to CSV files in the `data/` directory:

- `{epic}_{start_date}_{end_date}_{resolution}.csv`: Full dataset
- `{epic}_latest_{resolution}.csv`: Latest version (overwritten each time)

## Data Quality

The system implements several quality checks:

1. **Date Range Validation**: Ensures start date is before end date
2. **Duplicate Removal**: Removes duplicate timestamps
3. **Invalid Price Filtering**: Removes prices <= 0
4. **Missing Data Handling**: Handles missing bid/ask data
5. **Outlier Detection**: Logs warnings for suspicious data

## Rate Limiting

Capital.com API has strict rate limits. The system implements:

- Automatic rate limiting (0.5 seconds between requests)
- Chunked requests (30-day chunks for historical data)
- Retry logic for failed requests
- Delays between different commodity collections

## API Endpoints Used

The system uses three Capital.com API endpoints:

1. **Markets List**: `GET /api/v1/markets`
   - Returns list of available markets
   - Can filter by EPIC

2. **Market Details**: `GET /api/v1/markets/{epic}`
   - Returns detailed information about a specific market
   - Includes instrument details, trading rules, and current snapshot

3. **Prices**: `GET /api/v1/prices/{epic}`
   - Returns historical price data
   - Supports different time resolutions
   - Maximum 10,000 data points per request

## Example Response Data

### Market Details
```json
{
  "instrument": {
    "epic": "CRUDE_OIL",
    "symbol": "Crude Oil",
    "name": "Crude Oil",
    "type": "COMMODITIES",
    "currency": "USD",
    "lotSize": 1
  },
  "snapshot": {
    "marketStatus": "TRADEABLE",
    "bid": 75.5,
    "offer": 75.6,
    "high": 76.0,
    "low": 75.0
  }
}
```

### Price Data
```json
{
  "prices": [
    {
      "snapshotTimeUTC": "2024-01-01T00:00:00",
      "closePrice": {"bid": 75.5, "ask": 75.6},
      "highPrice": {"bid": 75.7, "ask": 75.8},
      "lowPrice": {"bid": 75.3, "ask": 75.4},
      "lastTradedVolume": 1000
    }
  ]
}
```

## Automation

### Daily Cron Job

Set up a daily cron job to automatically update data:

```bash
# Add to crontab (crontab -e)
0 2 * * * cd /path/to/pvpc.info && /path/to/python collect_commodities.py --update >> logs/commodity_cron.log 2>&1
```

### Systemd Timer (Linux)

Create a systemd service and timer:

```ini
# /etc/systemd/system/commodity-update.service
[Unit]
Description=Update commodity price data

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/pvpc.info
ExecStart=/path/to/python collect_commodities.py --update

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/commodity-update.timer
[Unit]
Description=Daily commodity data update

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable commodity-update.timer
sudo systemctl start commodity-update.timer
```

## Troubleshooting

### No Data Collected

1. Check if the EPIC code is correct in `src/config.py`
2. Verify the commodity is tradeable during the requested time period
3. Check API rate limits haven't been exceeded
4. Enable verbose logging: `--verbose`

### Database Errors

1. Ensure the data directory exists and is writable
2. Check database file isn't locked by another process
3. For PostgreSQL, verify connection string is correct

### Rate Limit Errors

1. Reduce the frequency of requests
2. Increase `CAPITAL_RATE_LIMIT` in `src/config.py`
3. Use larger chunk sizes for historical data

## Architecture

### Components

1. **CapitalClient** (`src/capital_client.py`):
   - Low-level API client
   - Handles HTTP requests and rate limiting
   - Parses API responses

2. **DatabaseManager** (`src/database.py`):
   - Database schema and operations
   - SQLAlchemy models
   - CRUD operations

3. **CommodityDataCollector** (`src/commodity_collector.py`):
   - High-level data collection logic
   - Data validation and cleaning
   - Orchestrates client and database operations

4. **CLI Script** (`collect_commodities.py`):
   - Command-line interface
   - Argument parsing
   - Logging setup

## Testing

Run the test suite:

```bash
# Run all commodity-related tests
pytest tests/test_capital_client.py tests/test_commodity_collector.py tests/test_database.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Best Practices

1. **Start Small**: Test with a single commodity and short date range first
2. **Use Updates**: After initial collection, use `--update` mode for efficiency
3. **Monitor Logs**: Check `logs/commodity_collection.log` regularly
4. **Backup Data**: Keep CSV backups of important data
5. **Database Maintenance**: Periodically check database size and optimize
6. **API Limits**: Be respectful of API rate limits
7. **Resolution Choice**: Use HOUR resolution for most use cases (good balance of detail and storage)

## Future Improvements

- [ ] Support for additional commodity markets
- [ ] Real-time streaming data support
- [ ] Advanced data analytics and visualization
- [ ] Integration with prediction models
- [ ] Web dashboard for monitoring
- [ ] Alerting system for significant price movements
- [ ] Multi-currency support
- [ ] Data export to other formats (Parquet, HDF5)

## References

- [Capital.com API Documentation](https://capital.com/api-development-guide)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pandas Documentation](https://pandas.pydata.org/)

## Support

For issues or questions:
1. Check the logs in `logs/commodity_collection.log`
2. Enable verbose mode for detailed debugging
3. Review the test suite for usage examples
4. Open an issue on GitHub
