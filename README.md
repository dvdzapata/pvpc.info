# pvpc.info

Web App de información sobre las tarifas PVPC de energia y datos sobre el mercado eléctrico español.

## Descripción del Proyecto

Este proyecto tiene como objetivo crear una plataforma completa para:

1. **Recolección de datos históricos** de precios PVPC (Precio Voluntario para el Pequeño Consumidor)
2. **Desarrollo de una API pública** para compartir datos de energía en España
3. **Predicción de precios** usando modelos TFT (Temporal Fusion Transformer) para 2, 5 y 7 días en el futuro
4. **Web y App** con visualización sencilla y clara de los precios de la energía

## Estado Actual: Recolección de Datos Históricos ✅

Hemos implementado la infraestructura para recolectar datos históricos de precios PVPC desde la API de ESIOS (Red Eléctrica de España).

### Características

- ✅ Cliente para la API de ESIOS
- ✅ Recolección de datos históricos con gestión automática de chunks
- ✅ Soporte para múltiples indicadores PVPC
- ✅ Almacenamiento en CSV
- ✅ Logging completo
- ✅ CLI para ejecutar la recolección

## Instalación

### Requisitos

- Python 3.8 o superior
- Token de API de ESIOS (gratuito)

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
# Editar .env y añadir tu token de ESIOS
```

4. Obtener token de API de ESIOS:
   - Visitar: https://www.esios.ree.es/en
   - Crear cuenta y solicitar un token de API

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

## Estructura del Proyecto

```
pvpc.info/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuración del proyecto
│   ├── esios_client.py     # Cliente para API de ESIOS
│   └── data_collector.py   # Lógica de recolección de datos
├── data/                   # Datos recolectados (CSV)
├── logs/                   # Logs de ejecución
├── tests/                  # Tests (próximamente)
├── collect_data.py         # Script CLI principal
├── requirements.txt        # Dependencias Python
├── .env.example           # Ejemplo de configuración
└── README.md              # Este archivo
```

## Datos Recolectados

Los datos se guardan en formato CSV en el directorio `data/` con la siguiente estructura:

- `{indicator}_YYYY-MM-DD_YYYY-MM-DD.csv`: Datos para el rango de fechas especificado
- `{indicator}_latest.csv`: Última versión de los datos recolectados

Formato de los datos:
- `datetime`: Fecha y hora (timezone: Europe/Madrid)
- `price_eur_mwh`: Precio en EUR/MWh
- `indicator_id`: ID del indicador
- `indicator_name`: Nombre del indicador

## Commodity Data Collection 🆕

Además de los datos PVPC, el proyecto ahora incluye un sistema completo para recolectar datos de mercado de commodities (petróleo, gas natural, emisiones de carbono) desde Capital.com API.

### Características

- ✅ Recolección de datos históricos de commodities (hasta 2 años)
- ✅ Soporte para múltiples resoluciones temporales (minuto, hora, día, semana)
- ✅ Base de datos SQLite con esquema automático
- ✅ Validación y limpieza de datos
- ✅ Actualizaciones diarias incrementales
- ✅ Control de rate limiting
- ✅ Tests completos

### Uso Rápido

```bash
# Recolectar todos los commodities (2 años de datos horarios)
python collect_commodities.py --commodity all

# Actualización diaria (solo nuevos datos)
python collect_commodities.py --update

# Recolectar commodity específico
python collect_commodities.py --commodity crude_oil_rt --resolution DAY
```

Ver [docs/COMMODITIES.md](docs/COMMODITIES.md) para documentación completa.

## Próximos Pasos

- [x] Implementar base de datos (SQLite/PostgreSQL) para almacenamiento eficiente
- [x] Añadir recolección de datos de commodities
- [x] Añadir tests automatizados
- [ ] Desarrollar API REST pública
- [ ] Implementar modelo TFT para predicciones
- [ ] Crear frontend web con visualizaciones
- [ ] Desarrollar aplicación móvil
- [ ] Configurar CI/CD

## Fuentes de Datos

- **ESIOS API**: https://www.esios.ree.es/en
- **Red Eléctrica de España (REE)**: Operador del sistema eléctrico español

## Licencia

Por definir

## Contribuciones

Por definir
