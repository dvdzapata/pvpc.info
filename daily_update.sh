#!/bin/bash
# Daily update script for ESIOS data collection
# Add to crontab: 0 1 * * * /path/to/daily_update.sh

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run daily update
echo "Starting daily ESIOS data update: $(date)"
python3 process_esios_indicators.py --daily-update --priority 3 --resume

echo "Daily update completed: $(date)"
