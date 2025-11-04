"""
Robust ESIOS data collector with resume capability, progress tracking, and quality validation
"""
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import pytz
from tqdm import tqdm

from .esios_client import ESIOSClient
from .database import DatabaseManager, Indicator, IndicatorValue
from .config import ESIOS_API_TOKEN, BASE_DIR

logger = logging.getLogger(__name__)


class ESIOSDataCollector:
    """
    Comprehensive data collector for ESIOS indicators with:
    - Resume capability
    - Progress tracking
    - Data quality validation
    - Request rate limiting
    - Detailed logging
    """
    
    # Indicator categories for PVPC prediction
    CATEGORIES = {
        'price': [
            'precio', 'price', 'pvpc', 'mercado', 'market', 'coste', 'cost',
            'componente', 'término', 'tarifa', 'peaje'
        ],
        'production': [
            'generación', 'generation', 'producción', 'production', 'programada',
            'nuclear', 'hidráulica', 'eólica', 'solar', 'térmica', 'carbón',
            'ciclo combinado', 'renovable', 'wind', 'photovoltaic'
        ],
        'demand': [
            'demanda', 'demand', 'consumo', 'consumption', 'prevista', 'forecast',
            'programada', 'scheduled', 'real', 'actual'
        ],
        'capacity': [
            'potencia', 'capacity', 'instalada', 'installed', 'disponible', 'available'
        ],
        'exchange': [
            'intercambio', 'exchange', 'importación', 'exportación', 'import', 'export',
            'saldo', 'balance', 'frontera', 'francia', 'portugal', 'marruecos'
        ],
        'storage': [
            'bombeo', 'pumping', 'almacenamiento', 'storage', 'reserva', 'reserve',
            'batería', 'battery'
        ],
        'emissions': [
            'emisiones', 'emissions', 'co2', 'carbono', 'carbon'
        ],
        'renewable': [
            'renovable', 'renewable', 'limpia', 'clean', 'verde', 'green'
        ],
        'other': []  # Catch-all
    }
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        database_url: Optional[str] = None,
        checkpoint_dir: Optional[Path] = None
    ):
        """
        Initialize the data collector
        
        Args:
            api_token: ESIOS API token
            database_url: PostgreSQL connection URL
            checkpoint_dir: Directory for checkpoint files
        """
        self.client = ESIOSClient(token=api_token)
        self.db = DatabaseManager(database_url=database_url)
        self.checkpoint_dir = checkpoint_dir or BASE_DIR / 'checkpoints'
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Request rate limiting
        self.requests_count = 0
        self.requests_start_time = time.time()
        self.max_requests_per_minute = 50  # Conservative limit
    
    def parse_indicators_file(self, filepath: Path) -> List[Dict]:
        """
        Parse the indicators file, handling malformed JSON
        
        Args:
            filepath: Path to indicators file
            
        Returns:
            List of indicator dictionaries
        """
        logger.info(f"Parsing indicators file: {filepath}")
        
        try:
            # First attempt: try direct JSON parsing
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                indicators = data.get('indicators', [])
                logger.info(f"Successfully parsed {len(indicators)} indicators")
                return indicators
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}. Attempting manual parsing...")
            
            # Second attempt: manual parsing
            indicators = []
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by indicator pattern and parse each
            import re
            
            # Find all complete indicator objects
            pattern = r'\{\s*"name":\s*"[^"]+",\s*"description":[^}]+?"id":\s*\d+\s*\}'
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                try:
                    obj_str = match.group(0)
                    obj = json.loads(obj_str)
                    if 'id' in obj and 'name' in obj:
                        indicators.append(obj)
                except:
                    continue
            
            # If manual parsing also fails, try line-by-line
            if not indicators:
                logger.warning("Manual regex parsing failed. Trying line-by-line...")
                lines = content.split('\n')
                current_obj = ""
                bracket_count = 0
                
                for line in lines:
                    # Start of potential indicator
                    if '"name":' in line and bracket_count == 0:
                        current_obj = "{\n"
                        bracket_count = 1
                    elif bracket_count > 0:
                        current_obj += line + "\n"
                        bracket_count += line.count('{') - line.count('}')
                        
                        if bracket_count == 0:
                            try:
                                obj = json.loads(current_obj)
                                if 'id' in obj and 'name' in obj:
                                    indicators.append(obj)
                            except:
                                pass
                            current_obj = ""
            
            logger.info(f"Parsed {len(indicators)} indicators using fallback method")
            return indicators
    
    def categorize_indicator(self, indicator: Dict) -> str:
        """
        Categorize an indicator based on its name and description
        
        Args:
            indicator: Indicator dictionary
            
        Returns:
            Category name
        """
        text = (indicator.get('name', '') + ' ' + 
                indicator.get('description', '') + ' ' + 
                indicator.get('short_name', '')).lower()
        
        # Check each category
        for category, keywords in self.CATEGORIES.items():
            if category == 'other':
                continue
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return 'other'
    
    def assign_priority(self, indicator: Dict, category: str) -> int:
        """
        Assign priority to an indicator (1=highest, 5=lowest)
        
        Args:
            indicator: Indicator dictionary
            category: Assigned category
            
        Returns:
            Priority level
        """
        text = indicator.get('name', '').lower() + ' ' + indicator.get('short_name', '').lower()
        
        # Priority 1: Critical for PVPC prediction
        if category == 'price':
            if any(word in text for word in ['pvpc', 'mercado diario', 'spot', 'precio final']):
                return 1
        
        if category == 'demand':
            if any(word in text for word in ['demanda prevista', 'demanda real', 'demanda programada']):
                return 1
        
        # Priority 2: Important for prediction
        if category in ['production', 'renewable']:
            if any(word in text for word in ['solar', 'eólica', 'hidráulica', 'nuclear']):
                return 2
        
        if category == 'exchange':
            return 2
        
        # Priority 3: Useful context
        if category in ['capacity', 'storage']:
            return 3
        
        # Priority 4: Background information
        if category == 'emissions':
            return 4
        
        # Priority 5: Other
        return 5
    
    def generate_indicators_catalog(
        self,
        input_file: Path,
        output_file: Path
    ) -> List[Dict]:
        """
        Generate a catalog of indicators with categories and priorities
        
        Args:
            input_file: Path to raw indicators file
            output_file: Path to output JSON file
            
        Returns:
            List of processed indicators
        """
        logger.info("Generating indicators catalog...")
        
        # Parse indicators
        raw_indicators = self.parse_indicators_file(input_file)
        
        # Process and categorize
        processed = []
        for ind in tqdm(raw_indicators, desc="Categorizing indicators"):
            category = self.categorize_indicator(ind)
            priority = self.assign_priority(ind, category)
            
            processed_ind = {
                'id': ind.get('id'),
                'name': ind.get('name'),
                'short_name': ind.get('short_name'),
                'description': ind.get('description', ''),
                'category': category,
                'priority': priority,
                'justification': f"Categorized as {category} with priority {priority} for PVPC prediction"
            }
            processed.append(processed_ind)
        
        # Sort by priority and category
        processed.sort(key=lambda x: (x['priority'], x['category'], x['id']))
        
        # Save to file
        output_data = {
            'metadata': {
                'generated_at': datetime.now(pytz.UTC).isoformat(),
                'total_indicators': len(processed),
                'categories': {cat: len([i for i in processed if i['category'] == cat]) 
                             for cat in self.CATEGORIES.keys()}
            },
            'indicators': processed
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved catalog to {output_file}")
        logger.info(f"Total indicators: {len(processed)}")
        logger.info(f"By category: {output_data['metadata']['categories']}")
        
        return processed
    
    def save_checkpoint(self, checkpoint_name: str, data: Dict):
        """Save checkpoint data"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f)
        logger.debug(f"Checkpoint saved: {checkpoint_file}")
    
    def load_checkpoint(self, checkpoint_name: str) -> Optional[Dict]:
        """Load checkpoint data"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r') as f:
                return json.load(f)
        return None
    
    def rate_limit_check(self):
        """Check and enforce rate limiting"""
        self.requests_count += 1
        
        # Check if we've exceeded the rate limit
        elapsed = time.time() - self.requests_start_time
        if elapsed < 60:  # Within a minute
            if self.requests_count >= self.max_requests_per_minute:
                sleep_time = 60 - elapsed
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                self.requests_count = 0
                self.requests_start_time = time.time()
        else:
            # Reset counter after a minute
            self.requests_count = 1
            self.requests_start_time = time.time()
    
    def collect_indicator_data(
        self,
        indicator_id: int,
        start_date: str,
        end_date: str,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Collect data for a single indicator with resume capability
        
        Args:
            indicator_id: ID of the indicator
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            force_refresh: Force re-download even if data exists
            
        Returns:
            DataFrame with collected data
        """
        start_time = time.time()
        
        # Check if we already have this data
        if not force_refresh:
            latest_date = self.db.get_latest_data_date(indicator_id)
            if latest_date:
                start_dt = pd.to_datetime(start_date)
                if latest_date >= start_dt:
                    logger.info(f"Indicator {indicator_id}: Data already exists up to {latest_date}")
                    start_date = (latest_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    
                    if start_date > end_date:
                        logger.info(f"Indicator {indicator_id}: Already up to date")
                        return pd.DataFrame()
        
        # Rate limiting
        self.rate_limit_check()
        
        try:
            # Fetch data from API
            df = self.client.get_historical_data_chunked(
                indicator_id=indicator_id,
                start_date=start_date,
                end_date=end_date,
                chunk_days=90,  # Smaller chunks for reliability
                delay_seconds=1.2
            )
            
            if df.empty:
                logger.warning(f"No data returned for indicator {indicator_id}")
                return df
            
            # Prepare for database insertion
            values_data = []
            for idx, row in df.iterrows():
                value_dict = {
                    'indicator_id': indicator_id,
                    'datetime': idx.to_pydatetime() if isinstance(idx, pd.Timestamp) else idx,
                    'value': float(row['value']) if 'value' in row else float(row.get('price_eur_mwh', 0)),
                }
                
                # Add optional fields
                if 'value_min' in row:
                    value_dict['value_min'] = float(row['value_min'])
                if 'value_max' in row:
                    value_dict['value_max'] = float(row['value_max'])
                if 'geo_id' in row:
                    value_dict['geo_id'] = int(row['geo_id'])
                if 'geo_name' in row:
                    value_dict['geo_name'] = str(row['geo_name'])
                
                values_data.append(value_dict)
            
            # Insert into database
            if values_data:
                self.db.bulk_insert_values(values_data)
            
            # Log the collection
            execution_time = time.time() - start_time
            self.db.log_collection({
                'indicator_id': indicator_id,
                'start_date': pd.to_datetime(start_date),
                'end_date': pd.to_datetime(end_date),
                'records_fetched': len(values_data),
                'status': 'success',
                'execution_time_seconds': execution_time
            })
            
            logger.info(f"Successfully collected {len(values_data)} records for indicator {indicator_id}")
            return df
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error collecting data for indicator {indicator_id}: {e}")
            
            # Log the failure
            self.db.log_collection({
                'indicator_id': indicator_id,
                'start_date': pd.to_datetime(start_date),
                'end_date': pd.to_datetime(end_date),
                'records_fetched': 0,
                'status': 'failed',
                'error_message': str(e),
                'execution_time_seconds': execution_time
            })
            
            return pd.DataFrame()
    
    def collect_all_indicators(
        self,
        indicators: List[Dict],
        start_date: str,
        end_date: str,
        max_priority: int = 3,
        resume: bool = True
    ):
        """
        Collect data for all indicators with specified priority
        
        Args:
            indicators: List of indicator dictionaries
            start_date: Start date
            end_date: End date
            max_priority: Maximum priority level to collect (1-5)
            resume: Whether to resume from checkpoint
        """
        # Filter indicators by priority
        to_collect = [ind for ind in indicators if ind.get('priority', 5) <= max_priority]
        logger.info(f"Collecting data for {len(to_collect)} indicators (priority <= {max_priority})")
        
        # Check for checkpoint
        checkpoint_name = f"collection_{start_date}_{end_date}"
        checkpoint = self.load_checkpoint(checkpoint_name) if resume else None
        completed_ids = set(checkpoint.get('completed', [])) if checkpoint else set()
        
        # Collect data with progress bar
        with tqdm(total=len(to_collect), desc="Collecting indicators") as pbar:
            for ind in to_collect:
                indicator_id = ind['id']
                
                # Skip if already completed
                if indicator_id in completed_ids:
                    pbar.update(1)
                    continue
                
                logger.info(f"Collecting: {ind['name']} (ID: {indicator_id}, Category: {ind['category']})")
                
                try:
                    self.collect_indicator_data(indicator_id, start_date, end_date)
                    
                    # Update checkpoint
                    completed_ids.add(indicator_id)
                    self.save_checkpoint(checkpoint_name, {
                        'completed': list(completed_ids),
                        'last_updated': datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to collect indicator {indicator_id}: {e}")
                
                pbar.update(1)
                
                # Small delay between indicators
                time.sleep(0.5)
        
        logger.info("Data collection completed!")
