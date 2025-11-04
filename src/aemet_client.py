"""
Client for interacting with the AEMET API (Agencia Estatal de Meteorología)
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging
import time

from .config import AEMET_API_TOKEN, AEMET_BASE_URL

logger = logging.getLogger(__name__)


class AEMETClient:
    """Client for the AEMET API to retrieve weather and climatological data"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the AEMET API client
        
        Args:
            token: API token for authentication. If not provided, uses config.
        
        Raises:
            ValueError: If no API token is provided
        """
        self.token = token if token is not None else AEMET_API_TOKEN
        if not self.token or self.token.strip() == '':
            raise ValueError(
                "No API token provided. Please:\n"
                "  1. Set AEMET_API_TOKEN in your .env file, or\n"
                "  2. Pass token parameter to AEMETClient(), or\n"
                "  3. Get a free token at https://opendata.aemet.es/centrodedescargas/inicio"
            )
        
        self.base_url = AEMET_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'api_key': self.token
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make a request to AEMET API
        
        AEMET API returns a URL to the actual data in most cases,
        so this method handles the two-step process.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
        
        Returns:
            JSON response data
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            # First request to get data URL
            response = self.session.get(url, params=params)
            response.raise_for_status()
            metadata = response.json()
            
            # Check if we got a data URL
            if isinstance(metadata, dict) and 'datos' in metadata:
                data_url = metadata['datos']
                # Second request to get actual data
                data_response = self.session.get(data_url)
                data_response.raise_for_status()
                return data_response.json()
            else:
                # Some endpoints return data directly
                return metadata
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {endpoint}: {e}")
            raise
    
    def get_climatological_series(
        self,
        start_date: str,
        end_date: str,
        station_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get climatological series data
        
        Note: AEMET API only allows requests for 6-month periods.
        This method automatically chunks the request.
        
        Args:
            start_date: Start date in format 'YYYY-MM-DD'
            end_date: End date in format 'YYYY-MM-DD'
            station_id: Optional station indicator code
        
        Returns:
            List of climatological data records
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        all_data = []
        current_start = start
        
        # AEMET allows max 6 months per request
        chunk_months = 6
        
        while current_start < end:
            # Calculate chunk end (6 months from start)
            current_end = min(
                current_start + pd.DateOffset(months=chunk_months),
                end
            )
            
            # Format dates as AEMET expects: YYYY-MM-DDTHH:MM:SSUTC
            start_str = current_start.strftime('%Y-%m-%dT00:00:00UTC')
            end_str = current_end.strftime('%Y-%m-%dT23:59:59UTC')
            
            try:
                endpoint = f"valores/climatologicos/diarios/datos/fechaini/{start_str}/fechafin/{end_str}/todasestaciones"
                if station_id:
                    endpoint = f"valores/climatologicos/diarios/datos/fechaini/{start_str}/fechafin/{end_str}/estacion/{station_id}"
                
                logger.info(f"Fetching climatological data from {start_str} to {end_str}")
                chunk_data = self._make_request(endpoint)
                
                if chunk_data and isinstance(chunk_data, list):
                    all_data.extend(chunk_data)
                
                # Move to next chunk
                current_start = current_end
                
                # Rate limiting - be respectful to the API
                if current_start < end:
                    time.sleep(1.0)
                    
            except Exception as e:
                logger.error(f"Error fetching chunk {start_str} to {end_str}: {e}")
                current_start = current_end
        
        return all_data
    
    def get_normal_values(self, station_id: str) -> Dict:
        """
        Get normal climatological values for a station
        
        Note: This endpoint does not support date filtering
        
        Args:
            station_id: Station indicator code
        
        Returns:
            Dictionary with normal values data
        """
        endpoint = f"valores/climatologicos/normales/estacion/{station_id}"
        return self._make_request(endpoint)
    
    def get_monthly_climatology(
        self,
        year: int,
        month: int,
        station_id: str
    ) -> Dict:
        """
        Get monthly climatology data
        
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            station_id: Station indicator code
        
        Returns:
            Dictionary with monthly climatology data
        """
        endpoint = f"valores/climatologicos/mensualesanuales/datos/anioini/{year}/aniofin/{year}/estacion/{station_id}"
        return self._make_request(endpoint)
    
    def get_temperature_extremes(
        self,
        station_id: str
    ) -> Dict:
        """
        Get extreme temperature records for a station
        
        Args:
            station_id: Station indicator code
        
        Returns:
            Dictionary with temperature extreme records
        """
        endpoint = f"valores/climatologicos/valoresextremos/parametro/T/estacion/{station_id}"
        return self._make_request(endpoint)
    
    def get_precipitation_extremes(
        self,
        station_id: str
    ) -> Dict:
        """
        Get extreme precipitation records for a station
        
        Args:
            station_id: Station indicator code
        
        Returns:
            Dictionary with precipitation extreme records
        """
        endpoint = f"valores/climatologicos/valoresextremos/parametro/P/estacion/{station_id}"
        return self._make_request(endpoint)
    
    def get_wind_extremes(
        self,
        station_id: str
    ) -> Dict:
        """
        Get extreme wind records for a station
        
        Args:
            station_id: Station indicator code
        
        Returns:
            Dictionary with wind extreme records
        """
        endpoint = f"valores/climatologicos/valoresextremos/parametro/V/estacion/{station_id}"
        return self._make_request(endpoint)
    
    def get_weather_prediction(
        self,
        municipality_code: str
    ) -> Dict:
        """
        Get hourly weather prediction for a municipality
        
        Args:
            municipality_code: Municipality code (5 digits)
        
        Returns:
            Dictionary with weather prediction data
        """
        endpoint = f"prediccion/especifica/municipio/horaria/{municipality_code}"
        return self._make_request(endpoint)
    
    def get_stations_list(self) -> List[Dict]:
        """
        Get list of all weather stations
        
        Returns:
            List of station metadata
        """
        endpoint = "valores/climatologicos/inventarioestaciones/todasestaciones"
        return self._make_request(endpoint)
    
    def climatological_to_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """
        Convert climatological series data to pandas DataFrame
        
        Args:
            data: List of climatological records from API
        
        Returns:
            DataFrame with climatological data
        """
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert fecha to datetime
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
            df.set_index('fecha', inplace=True)
        
        # Convert numeric columns (they come as strings with commas)
        numeric_columns = [
            'tmed', 'prec', 'tmin', 'tmax', 'velmedia', 'racha', 'sol',
            'presMax', 'presMin', 'hrMedia', 'hrMax', 'hrMin'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                # Replace comma with dot and convert to float
                # Use pd.to_numeric with errors='coerce' to handle invalid values
                df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
        
        return df
