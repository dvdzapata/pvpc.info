# ESIOS Data Collection System

## Overview

This system provides a robust, production-ready solution for collecting and storing ESIOS (Red Eléctrica de España) indicator data for PVPC price prediction using Temporal Fusion Transformer (TFT) models.

## Features

- ✅ **Robust Parsing**: Handles malformed JSON in indicators file
- ✅ **Smart Categorization**: Automatically categorizes 1970+ indicators into relevant groups
- ✅ **Priority System**: 5-level priority system (1=critical, 5=low)
- ✅ **Resume Capability**: Checkpoint system allows resuming interrupted downloads
- ✅ **Progress Tracking**: Visual progress bars with tqdm
- ✅ **Rate Limiting**: Respects API limits (50 requests/minute)
- ✅ **Data Quality Validation**: Obsessive quality checks on completeness and consistency
- ✅ **PostgreSQL Storage**: Optimized schema with indexes for fast queries
- ✅ **Detailed Logging**: Comprehensive logs for debugging and monitoring
- ✅ **Daily Updates**: Automated daily data collection
- ✅ **Error Recovery**: Automatic retry and error logging

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    process_esios_indicators.py                   │
│                     (Main Executable Script)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│ esios_data_     │  │ database.py  │  │ esios_client.py │
│ collector.py    │  │              │  │                 │
│                 │  │ - Models     │  │ - API calls     │
│ - Parsing       │  │ - Schemas    │  │ - Rate limit    │
│ - Categories    │  │ - Quality    │  │ - Chunking      │
│ - Checkpoints   │  │   checks     │  │                 │
└─────────────────┘  └──────────────┘  └─────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
                    ┌────────────────┐
                    │  PostgreSQL 16 │
                    │                │
                    │ - indicators   │
                    │ - values       │
                    │ - logs         │
                    └────────────────┘
```

## Database Schema

### indicators
Stores metadata about each indicator:
- `id` (PK): ESIOS indicator ID
- `name`: Full name
- `short_name`: Short name
- `description`: Full description
- `category`: Assigned category (price, production, demand, etc.)
- `priority`: Priority level (1-5)
- `is_active`: Whether to actively collect this indicator

### indicator_values
Stores time-series data:
- `id` (PK): Auto-increment
- `indicator_id`: Reference to indicator
- `datetime`: Timestamp (indexed)
- `value`: Main value
- `value_min`, `value_max`: Optional range values
- `geo_id`, `geo_name`: Geographic information (for provincial data)

### data_collection_logs
Tracks all collection operations:
- `indicator_id`: Which indicator
- `start_date`, `end_date`: Date range
- `records_fetched`: Number of records
- `status`: success/failed/partial
- `execution_time_seconds`: Performance tracking

## Categories

Indicators are automatically categorized for PVPC prediction:

1. **price** (Priority 1): Energy pricing, PVPC, market prices
2. **production** (Priority 2): Generation by type (solar, wind, nuclear, etc.)
3. **demand** (Priority 1-2): Forecasted vs actual demand
4. **capacity** (Priority 3): Installed capacity by type
5. **exchange** (Priority 2): International exchanges (FR, PT, MA)
6. **storage** (Priority 3): Pumping, batteries
7. **renewable** (Priority 2): Renewable generation percentage
8. **emissions** (Priority 4): CO2 emissions
9. **other** (Priority 5): Miscellaneous

## Usage

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
createdb esios_data

# Configure environment
cp .env.example .env
# Edit .env and add your ESIOS_API_TOKEN
```

### Initial Setup

```bash
# 1. Initialize database
python3 process_esios_indicators.py --init-db

# 2. Generate indicators catalog (no download)
python3 process_esios_indicators.py --catalog-only

# This creates: indicators-pack1.json
```

### Data Collection

```bash
# Collect high-priority data (Priority 1-2: prices, demand, production)
python3 process_esios_indicators.py \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --priority 2

# Collect medium-priority data (Priority 1-3: includes capacity, storage)
python3 process_esios_indicators.py \
    --start-date 2024-01-01 \
    --priority 3 \
    --resume

# Resume interrupted download
python3 process_esios_indicators.py \
    --start-date 2024-01-01 \
    --resume
```

### Daily Updates

```bash
# Manual daily update (yesterday's data)
python3 process_esios_indicators.py --daily-update

# Set up automatic daily updates (crontab)
crontab -e
# Add this line (runs at 1 AM daily):
0 1 * * * /path/to/pvpc.info/daily_update.sh >> /path/to/logs/cron.log 2>&1
```

## Output Files

### indicators-pack1.json
Comprehensive catalog of all indicators with:
- ID, name, short_name, description
- Assigned category
- Priority level
- Justification for categorization

Example:
```json
{
  "metadata": {
    "generated_at": "2025-11-04T04:57:00",
    "total_indicators": 1970,
    "categories": {
      "price": 245,
      "production": 187,
      "demand": 89,
      ...
    }
  },
  "indicators": [
    {
      "id": 1001,
      "name": "PVPC 2.0TD",
      "short_name": "PVPC 2.0TD",
      "description": "...",
      "category": "price",
      "priority": 1,
      "justification": "Critical for PVPC prediction"
    },
    ...
  ]
}
```

### Log Files
Located in `logs/esios_YYYYMMDD_HHMMSS.log`

Format:
```
2025-11-04 05:00:00 - INFO - Step 1: Generating indicators catalog
2025-11-04 05:00:15 - INFO - Parsed 1970 indicators
2025-11-04 05:00:20 - INFO - Step 2: Collecting indicator data
2025-11-04 05:00:21 - INFO - Collecting: PVPC 2.0TD (ID: 1001, Category: price)
2025-11-04 05:00:45 - INFO - Successfully collected 8760 records for indicator 1001
...
```

## Data Quality Validation

The system performs **obsessive** quality checks:

1. **Completeness**: Verifies all expected hours have data
2. **Null Checks**: Counts and reports missing values
3. **Range Validation**: Checks min/max values are reasonable
4. **Duplicate Detection**: Removes duplicate timestamps
5. **Continuity**: Ensures no gaps in time series

Quality metrics are logged for every collection:
```python
{
    'record_count': 8760,
    'null_count': 0,
    'min_value': 12.45,
    'max_value': 189.32,
    'avg_value': 87.63,
    'completeness': 1.0  # 100%
}
```

## API Rate Limiting

- Conservative limit: 50 requests/minute
- Automatic sleep when limit reached
- Exponential backoff on errors
- Checkpoint system ensures no duplicate requests

## Resume Capability

The system uses checkpoints stored in `checkpoints/`:

```json
{
  "completed": [1, 2, 3, 4, 5, ...],
  "last_updated": "2025-11-04T05:30:00"
}
```

If interrupted:
1. Ctrl+C safely saves progress
2. Run with `--resume` to continue
3. Already-fetched data is skipped
4. No duplicate API calls

## Error Handling

All errors are:
1. Logged with full stack trace
2. Recorded in `data_collection_logs` table
3. Retried with exponential backoff
4. Reported in daily summary

## Performance

- ~1.2 seconds per API request (rate limiting)
- ~50 indicators per minute
- ~3000 indicators/hour
- Full collection (priority 1-3, ~800 indicators, 1 year): ~16 hours

## Monitoring

Query the database to monitor progress:

```sql
-- Check collection status
SELECT 
    status,
    COUNT(*) as count,
    SUM(records_fetched) as total_records
FROM data_collection_logs
WHERE created_at >= NOW() - INTERVAL '1 day'
GROUP BY status;

-- Top indicators by data volume
SELECT 
    i.short_name,
    COUNT(*) as records,
    MIN(iv.datetime) as first_date,
    MAX(iv.datetime) as last_date
FROM indicators i
JOIN indicator_values iv ON i.id = iv.indicator_id
GROUP BY i.id, i.short_name
ORDER BY records DESC
LIMIT 10;

-- Data quality summary
SELECT 
    i.category,
    COUNT(DISTINCT i.id) as indicators,
    COUNT(iv.id) as total_records,
    AVG(iv.value) as avg_value
FROM indicators i
JOIN indicator_values iv ON i.id = iv.indicator_id
GROUP BY i.category
ORDER BY indicators DESC;
```

## Troubleshooting

### "No API token provided"
Solution: Set `ESIOS_API_TOKEN` in `.env` or use `--api-token`

### "Database connection failed"
Solution: Check PostgreSQL is running and `DATABASE_URL` is correct

### "JSON decode error"
Solution: The script handles this automatically with fallback parsing

### "Rate limit exceeded"
Solution: Script automatically sleeps. Reduce `max_requests_per_minute` if needed.

### Slow download
Solution: Normal. Full download takes ~16 hours due to rate limiting.

## Integration with TFT Model

This data collection system provides all necessary inputs for the TFT predictive model:

**Target Variable:**
- PVPC prices (hourly)

**Known Future Inputs:**
- Hour of day
- Day of week
- Month
- Holidays

**Unknown Future Inputs (to be predicted):**
- Renewable generation
- Total demand
- Exchange balance

**Static Covariates:**
- Installed capacity by type
- Geographic distribution

## Next Steps

1. ✅ Initial data collection (Priority 1-2, 2024 data)
2. ⏳ Validate data quality
3. ⏳ Develop TFT model
4. ⏳ Create API endpoints
5. ⏳ Build web frontend

## Support

For issues or questions:
1. Check log files in `logs/`
2. Review `indicators-pack1.json` for available indicators
3. Query `data_collection_logs` table for errors
4. Open GitHub issue with log excerpt
