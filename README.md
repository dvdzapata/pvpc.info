# pvpc.info

Web App de información sobre las tarifas PVPC de energia y datos sobre el mercado eléctrico español.

## Descripción del Proyecto

Este proyecto tiene como objetivo crear una plataforma completa para:

1. **Recolección de datos históricos** de precios PVPC (Precio Voluntario para el Pequeño Consumidor)
2. **Desarrollo de una API pública** para compartir datos de energía en España
3. **Predicción de precios** usando modelos TFT (Temporal Fusion Transformer) para 2, 5 y 7 días en el futuro
4. **Web y App** con visualización sencilla y clara de los precios de la energía

## Estado Actual: Recolección de Datos Históricos ✅

Hemos implementado la infraestructura para recolectar datos históricos de precios PVPC desde la API de ESIOS (Red Eléctrica de España) y datos climatológicos desde la API de AEMET (Agencia Estatal de Meteorología).

### Características

- ✅ Cliente para la API de ESIOS (precios de electricidad)
- ✅ Cliente para la API de AEMET (datos climatológicos)
- ✅ Recolección de datos históricos con gestión automática de chunks
- ✅ Soporte para múltiples indicadores PVPC
- ✅ Soporte para datos meteorológicos (temperatura, precipitación, viento, etc.)
- ✅ Almacenamiento en CSV
- ✅ Logging completo
- ✅ CLI para ejecutar la recolección

## Instalación

### Requisitos

- Python 3.8 o superior
- Token de API de ESIOS (gratuito)
- Token de API de AEMET (gratuito)

### Configuración

1. Clonar el repositorio:
```bash
git clone https://github.com/dvdzapata/pvpc.info.git
cd pvpc.info
```

2. Crear un entorno virtual e instalar dependencias:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env y añadir tus tokens de ESIOS y AEMET
```

4. Obtener tokens de API:
   - **ESIOS**: Visitar https://www.esios.ree.es/en y solicitar un token
   - **AEMET**: Visitar https://opendata.aemet.es/centrodedescargas/inicio y solicitar un token

## Uso

### Recolectar Datos Históricos

```bash
# Recolectar datos PVPC 2.0TD (tarifa residencial más común)
python collect_data.py --start-date 2021-01-01 --end-date 2024-12-31

# Recolectar todos los indicadores disponibles
python collect_data.py --indicator all --start-date 2023-01-01

# Especificar token de API directamente
python collect_data.py --token YOUR_TOKEN_HERE --start-date 2023-01-01

# Modo verbose para más información
python collect_data.py --verbose
```

### Indicadores Disponibles

- `pvpc_2.0TD` (ID: 1001): PVPC 2.0TD - Tarifa residencial más común
- `pvpc_spot` (ID: 600): Precio del mercado diario (SPOT)
- `pvpc_base` (ID: 1739): Precio base PVPC

### Recolectar Datos Climatológicos (AEMET)

```python
from src.aemet_client import AEMETClient

# Inicializar cliente
client = AEMETClient(token="tu_token_aquí")

# Obtener series climatológicas (automáticamente dividido en chunks de 6 meses)
data = client.get_climatological_series('2021-01-01', '2024-12-31', station_id='9091R')

# Convertir a DataFrame para análisis
df = client.climatological_to_dataframe(data)

# Obtener valores normales (promedios históricos)
normal_values = client.get_normal_values('9091R')

# Obtener climatología mensual
monthly = client.get_monthly_climatology(2024, 10, '5402')

# Obtener registros extremos
temp_extremes = client.get_temperature_extremes('5402')
precip_extremes = client.get_precipitation_extremes('5402')
wind_extremes = client.get_wind_extremes('5402')

# Obtener predicción meteorológica
prediction = client.get_weather_prediction('01037')

# Listar estaciones disponibles
stations = client.get_stations_list()
```

### Endpoints AEMET Disponibles

- **Series Climatológicas**: Datos diarios históricos (temperatura, precipitación, viento, humedad, presión, etc.)
  - Máximo 6 meses por petición (gestionado automáticamente)
- **Valores Normales**: Promedios históricos mensuales por estación
- **Climatologías Mensuales/Anuales**: Resúmenes mensuales y anuales
- **Valores Extremos**: Registros históricos de temperatura, precipitación y viento
- **Predicciones**: Previsión meteorológica horaria por municipio

## Estructura del Proyecto

```
pvpc.info/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuración del proyecto
│   ├── esios_client.py     # Cliente para API de ESIOS
│   ├── aemet_client.py     # Cliente para API de AEMET
│   └── data_collector.py   # Lógica de recolección de datos
├── data/                   # Datos recolectados (CSV)
├── logs/                   # Logs de ejecución
├── tests/                  # Tests unitarios y de integración
├── collect_data.py         # Script CLI principal
├── requirements.txt        # Dependencias Python
├── .env.example           # Ejemplo de configuración
└── README.md              # Este archivo
```

## Datos Recolectados

### Datos ESIOS (Precios)

Los datos se guardan en formato CSV en el directorio `data/` con la siguiente estructura:

- `{indicator}_YYYY-MM-DD_YYYY-MM-DD.csv`: Datos para el rango de fechas especificado
- `{indicator}_latest.csv`: Última versión de los datos recolectados

Formato de los datos:
- `datetime`: Fecha y hora (timezone: Europe/Madrid)
- `price_eur_mwh`: Precio en EUR/MWh
- `indicator_id`: ID del indicador
- `indicator_name`: Nombre del indicador

### Datos AEMET (Climatología)

Datos disponibles de series climatológicas diarias:
- `fecha`: Fecha del registro
- `tmed`: Temperatura media (°C)
- `tmin`/`tmax`: Temperatura mínima/máxima (°C)
- `prec`: Precipitación (mm)
- `velmedia`: Velocidad media del viento (km/h)
- `racha`: Racha máxima del viento (km/h)
- `sol`: Horas de sol
- `presMax`/`presMin`: Presión máxima/mínima (hPa)
- `hrMedia`: Humedad relativa media (%)

## Próximos Pasos

- [ ] Implementar base de datos (SQLite/PostgreSQL) para almacenamiento eficiente
- [ ] Desarrollar API REST pública
- [ ] Implementar modelo TFT para predicciones
- [ ] Crear frontend web con visualizaciones
- [ ] Desarrollar aplicación móvil
- [ ] Añadir tests automatizados
- [ ] Configurar CI/CD

## Fuentes de Datos

- **ESIOS API**: https://www.esios.ree.es/en
  - Red Eléctrica de España (REE): Operador del sistema eléctrico español
  - Datos de precios PVPC y mercado eléctrico
- **AEMET OpenData**: https://opendata.aemet.es
  - Agencia Estatal de Meteorología
  - Datos climatológicos históricos y predicciones meteorológicas

## Licencia

Por definir

## Contribuciones

Por definir
