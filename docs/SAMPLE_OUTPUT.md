# Ejemplo de Salida de Datos

## Estructura de Archivos CSV

### Ejemplo: pvpc_2.0TD_2024-01-01_2024-01-31.csv

```csv
datetime,price_eur_mwh,indicator_id,indicator_name
2024-01-01 00:00:00+01:00,89.45,1001,PVPC 2.0TD
2024-01-01 01:00:00+01:00,87.32,1001,PVPC 2.0TD
2024-01-01 02:00:00+01:00,85.12,1001,PVPC 2.0TD
2024-01-01 03:00:00+01:00,83.98,1001,PVPC 2.0TD
2024-01-01 04:00:00+01:00,82.45,1001,PVPC 2.0TD
2024-01-01 05:00:00+01:00,84.23,1001,PVPC 2.0TD
2024-01-01 06:00:00+01:00,91.56,1001,PVPC 2.0TD
2024-01-01 07:00:00+01:00,98.76,1001,PVPC 2.0TD
2024-01-01 08:00:00+01:00,105.34,1001,PVPC 2.0TD
2024-01-01 09:00:00+01:00,112.45,1001,PVPC 2.0TD
2024-01-01 10:00:00+01:00,118.67,1001,PVPC 2.0TD
2024-01-01 11:00:00+01:00,121.23,1001,PVPC 2.0TD
2024-01-01 12:00:00+01:00,119.45,1001,PVPC 2.0TD
2024-01-01 13:00:00+01:00,116.78,1001,PVPC 2.0TD
2024-01-01 14:00:00+01:00,115.23,1001,PVPC 2.0TD
2024-01-01 15:00:00+01:00,113.67,1001,PVPC 2.0TD
2024-01-01 16:00:00+01:00,111.45,1001,PVPC 2.0TD
2024-01-01 17:00:00+01:00,109.89,1001,PVPC 2.0TD
2024-01-01 18:00:00+01:00,125.34,1001,PVPC 2.0TD
2024-01-01 19:00:00+01:00,131.56,1001,PVPC 2.0TD
2024-01-01 20:00:00+01:00,135.67,1001,PVPC 2.0TD
2024-01-01 21:00:00+01:00,128.45,1001,PVPC 2.0TD
2024-01-01 22:00:00+01:00,115.23,1001,PVPC 2.0TD
2024-01-01 23:00:00+01:00,102.45,1001,PVPC 2.0TD
```

## Descripción de Campos

### datetime
- **Tipo**: Timestamp con timezone
- **Timezone**: Europe/Madrid (CET/CEST)
- **Formato**: ISO 8601
- **Frecuencia**: Horaria
- **Notas**: Incluye ajustes por cambio de horario verano/invierno

### price_eur_mwh
- **Tipo**: Float
- **Unidad**: EUR/MWh (Euros por Megavatio-hora)
- **Rango típico**: 20-300 EUR/MWh
- **Decimales**: 2
- **Notas**: 
  - Valores negativos son posibles (exceso de renovables)
  - Picos pueden superar 300 EUR/MWh en situaciones extremas

### indicator_id
- **Tipo**: Integer
- **Valores comunes**:
  - 1001: PVPC 2.0TD
  - 600: Precio SPOT
  - 1739: PVPC Base

### indicator_name
- **Tipo**: String
- **Descripción**: Nombre descriptivo del indicador

## Análisis de Ejemplo

Para el día ejemplo (2024-01-01):

- **Precio mínimo**: 82.45 EUR/MWh (04:00 - madrugada)
- **Precio máximo**: 135.67 EUR/MWh (20:00 - hora punta)
- **Precio medio**: 107.98 EUR/MWh
- **Volatilidad**: Alta (rango de 53.22 EUR/MWh)

## Patrones Típicos

### Valle (Madrugada)
- **Horas**: 02:00 - 06:00
- **Precios**: Bajos (< 90 EUR/MWh)
- **Razón**: Baja demanda, alta producción renovable

### Llano (Día)
- **Horas**: 07:00 - 17:00
- **Precios**: Medios (90-120 EUR/MWh)
- **Razón**: Demanda moderada, producción solar

### Punta (Tarde-Noche)
- **Horas**: 18:00 - 22:00
- **Precios**: Altos (> 120 EUR/MWh)
- **Razón**: Máxima demanda, menor producción renovable

## Uso en Análisis

### Python/Pandas

```python
import pandas as pd

# Leer datos
df = pd.read_csv('pvpc_2.0TD_latest.csv', 
                 index_col='datetime', 
                 parse_dates=True)

# Análisis básico
print(f"Precio medio: {df['price_eur_mwh'].mean():.2f} EUR/MWh")
print(f"Precio mínimo: {df['price_eur_mwh'].min():.2f} EUR/MWh")
print(f"Precio máximo: {df['price_eur_mwh'].max():.2f} EUR/MWh")

# Análisis por hora del día
hourly_avg = df.groupby(df.index.hour)['price_eur_mwh'].mean()
print("\nPrecio medio por hora:")
print(hourly_avg)

# Análisis por día de la semana
daily_avg = df.groupby(df.index.dayofweek)['price_eur_mwh'].mean()
print("\nPrecio medio por día de la semana:")
print(daily_avg)
```

### R

```r
library(readr)
library(dplyr)
library(lubridate)

# Leer datos
df <- read_csv('pvpc_2.0TD_latest.csv')
df$datetime <- ymd_hms(df$datetime)

# Análisis básico
summary(df$price_eur_mwh)

# Análisis por hora del día
hourly_avg <- df %>%
  mutate(hour = hour(datetime)) %>%
  group_by(hour) %>%
  summarise(avg_price = mean(price_eur_mwh))

print(hourly_avg)
```

## Formatos Alternativos

Los datos también pueden exportarse a:

- **JSON**: Para APIs y aplicaciones web
- **Parquet**: Para procesamiento eficiente de big data
- **SQLite/PostgreSQL**: Para consultas complejas
- **Excel**: Para usuarios no técnicos

## Actualizaciones

Los archivos `*_latest.csv` se actualizan cada vez que se ejecuta la recolección, manteniendo siempre la versión más reciente de los datos históricos.
