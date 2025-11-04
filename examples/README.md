# Examples

This directory contains example scripts demonstrating how to use the collected PVPC data.

## Available Examples

### 1. analyze_prices.py

A comprehensive analysis script that demonstrates:

- Loading PVPC data from CSV
- Basic statistical analysis
- Hourly and daily price patterns
- Monthly trends
- Price distribution analysis
- Creating visualizations (time series, bar charts, heatmaps)
- Calculating potential savings

**Usage:**

```bash
# First, collect some data
cd ..
python collect_data.py --start-date 2024-01-01

# Then run the analysis
cd examples
python analyze_prices.py
```

**Output:**

- Console statistics and insights
- Visualization plots saved in the `examples/` directory:
  - `price_timeseries.png` - Recent price evolution
  - `hourly_pattern.png` - Average price by hour
  - `price_distribution.png` - Price histogram
  - `price_heatmap.png` - Hour-by-day heatmap

## Creating Your Own Analysis

### Basic Template

```python
import pandas as pd
from pathlib import Path

# Load data
df = pd.read_csv('../data/pvpc_2.0TD_latest.csv', 
                 index_col='datetime', 
                 parse_dates=True)

# Your analysis here
print(f"Average price: {df['price_eur_mwh'].mean():.2f} EUR/MWh")

# Find cheapest hours
hourly_avg = df.groupby(df.index.hour)['price_eur_mwh'].mean()
print(f"Cheapest hour: {hourly_avg.idxmin()}:00")
```

### Advanced Analysis Ideas

1. **Seasonal Patterns**
   ```python
   seasonal = df.groupby(df.index.month)['price_eur_mwh'].mean()
   ```

2. **Weekend vs Weekday**
   ```python
   df['is_weekend'] = df.index.dayofweek >= 5
   weekend_avg = df.groupby('is_weekend')['price_eur_mwh'].mean()
   ```

3. **Price Volatility**
   ```python
   daily_volatility = df.groupby(df.index.date)['price_eur_mwh'].std()
   ```

4. **Cost Optimization**
   ```python
   # Find best hours for specific consumption
   consumption_profile = {...}  # Hour: kWh
   total_cost = sum(df.loc[df.index.hour == h, 'price_eur_mwh'].mean() * kwh 
                    for h, kwh in consumption_profile.items())
   ```

## Using Data in Other Languages

### R Example

```r
library(readr)
library(dplyr)
library(ggplot2)

# Load data
df <- read_csv('../data/pvpc_2.0TD_latest.csv')
df$datetime <- as.POSIXct(df$datetime)

# Analysis
summary(df$price_eur_mwh)

# Visualization
ggplot(df, aes(x=datetime, y=price_eur_mwh)) +
  geom_line() +
  theme_minimal() +
  labs(title="PVPC Price Evolution", 
       y="Price (EUR/MWh)")
```

### JavaScript/Node.js Example

```javascript
const fs = require('fs');
const csv = require('csv-parser');

const prices = [];

fs.createReadStream('../data/pvpc_2.0TD_latest.csv')
  .pipe(csv())
  .on('data', (row) => {
    prices.push({
      datetime: new Date(row.datetime),
      price: parseFloat(row.price_eur_mwh)
    });
  })
  .on('end', () => {
    const avgPrice = prices.reduce((sum, p) => sum + p.price, 0) / prices.length;
    console.log(`Average price: ${avgPrice.toFixed(2)} EUR/MWh`);
  });
```

## Requirements

To run the examples, ensure you have installed all dependencies:

```bash
pip install -r ../requirements.txt
```

For visualization examples, you'll need matplotlib:

```bash
pip install matplotlib
```

## Contributing Examples

Have a useful analysis or visualization? Consider contributing!

1. Create a new Python script in this directory
2. Add clear documentation and comments
3. Update this README with your example
4. Submit a pull request

## Tips

- Always check if data exists before running analysis
- Handle missing data gracefully
- Comment your code for clarity
- Save important visualizations
- Consider memory usage for large datasets

## Support

For questions or issues with examples:
- Open an issue on GitHub
- Check the main documentation in `../docs/`
- Review the QUICKSTART.md guide
