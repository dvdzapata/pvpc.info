"""
Example script for collecting AEMET climatological data

This script demonstrates how to use the AEMETClient to retrieve
weather and climatological data from the Spanish meteorological agency.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.aemet_client import AEMETClient
from src.config import DATA_DIR


def main():
    """Main function to demonstrate AEMET data collection"""
    
    # Initialize the AEMET client
    # Token will be read from .env file
    try:
        client = AEMETClient()
        print("✅ AEMET client initialized successfully")
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Example 1: Get climatological series for a station
    print("\n" + "="*60)
    print("Example 1: Climatological Series")
    print("="*60)
    print("Fetching climatological data for station 9091R (Vitoria-Gasteiz)")
    print("Date range: 2023-01-01 to 2023-06-30")
    
    try:
        data = client.get_climatological_series(
            '2023-01-01',
            '2023-06-30',
            station_id='9091R'
        )
        print(f"✅ Retrieved {len(data)} daily records")
        
        if data:
            # Convert to DataFrame for better display
            df = client.climatological_to_dataframe(data)
            print("\nFirst 5 records:")
            print(df.head())
            
            # Save to CSV
            output_file = DATA_DIR / 'aemet_vitoria_2023.csv'
            df.to_csv(output_file)
            print(f"\n💾 Data saved to: {output_file}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Get normal values (historical averages)
    print("\n" + "="*60)
    print("Example 2: Normal Values (Historical Averages)")
    print("="*60)
    print("Fetching normal values for station 8178D")
    
    try:
        normal_values = client.get_normal_values('8178D')
        print(f"✅ Retrieved normal values")
        print(f"Station: {normal_values.get('indicativo', 'N/A')}")
        print(f"Month: {normal_values.get('mes', 'N/A')}")
        print(f"Max wind gust: {normal_values.get('w_racha_max', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 3: Get extreme temperature records
    print("\n" + "="*60)
    print("Example 3: Temperature Extremes")
    print("="*60)
    print("Fetching temperature extremes for station 5402 (Córdoba)")
    
    try:
        extremes = client.get_temperature_extremes('5402')
        print(f"✅ Retrieved temperature extremes")
        print(f"Station: {extremes.get('nombre', 'N/A')}")
        print(f"Location: {extremes.get('ubicacion', 'N/A')}")
        
        if 'temMax' in extremes and extremes['temMax']:
            # Temperature values are in tenths of degrees Celsius
            max_temp = float(extremes['temMax'][-1]) / 10
            print(f"Absolute maximum temperature: {max_temp}°C")
        
        if 'temMin' in extremes and extremes['temMin']:
            min_temp = float(extremes['temMin'][0]) / 10
            print(f"Absolute minimum temperature: {min_temp}°C")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 4: Get weather prediction
    print("\n" + "="*60)
    print("Example 4: Weather Prediction")
    print("="*60)
    print("Fetching weather prediction for municipality 01037")
    
    try:
        prediction = client.get_weather_prediction('01037')
        print(f"✅ Retrieved weather prediction")
        print(f"Municipality: {prediction.get('nombre', 'N/A')}")
        print(f"Province: {prediction.get('provincia', 'N/A')}")
        
        if 'prediccion' in prediction and 'dia' in prediction['prediccion']:
            days = prediction['prediccion']['dia']
            print(f"Prediction days: {len(days)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 5: List available stations
    print("\n" + "="*60)
    print("Example 5: List Weather Stations")
    print("="*60)
    print("Fetching list of available weather stations...")
    
    try:
        stations = client.get_stations_list()
        print(f"✅ Retrieved {len(stations)} weather stations")
        
        # Show first 5 stations
        print("\nFirst 5 stations:")
        for i, station in enumerate(stations[:5], 1):
            print(f"{i}. {station.get('nombre', 'N/A')} ({station.get('indicativo', 'N/A')}) - {station.get('provincia', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ Examples completed!")
    print("="*60)


if __name__ == '__main__':
    main()
