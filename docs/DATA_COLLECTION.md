# Guía de Recolección de Datos PVPC

## Introducción

Este documento describe el proceso de recolección de datos históricos de precios PVPC (Precio Voluntario para el Pequeño Consumidor) desde la API de ESIOS (Red Eléctrica de España).

## ¿Qué es PVPC?

El PVPC es el precio regulado de la electricidad en España para consumidores domésticos. Este precio varía cada hora según:

- La oferta y demanda del mercado eléctrico
- Los costes de transporte y distribución
- Los impuestos aplicables
- Los cargos del sistema eléctrico

## API de ESIOS

### Descripción

ESIOS (Sistema de Información del Operador del Sistema) es la plataforma oficial de Red Eléctrica de España que proporciona acceso a datos del mercado eléctrico español.

### Autenticación

Para usar la API necesitas:

1. Crear una cuenta en https://www.esios.ree.es
2. Solicitar un token de API (gratuito)
3. Incluir el token en las peticiones mediante el header `x-api-key`

### Endpoints Principales

- `GET /indicators`: Lista todos los indicadores disponibles
- `GET /indicators/{id}`: Obtiene datos de un indicador específico

### Parámetros de Consulta

- `start_date`: Fecha de inicio (formato: YYYY-MM-DDTHH:MM:SS)
- `end_date`: Fecha de fin (formato: YYYY-MM-DDTHH:MM:SS)
- `time_trunc`: Agregación temporal (hour, day, month)

## Indicadores PVPC

### 1001 - PVPC 2.0TD

El indicador más importante para usuarios domésticos. Incluye:

- Precio de la energía en el mercado diario
- Cargos por servicios de ajuste
- Pagos por capacidad
- Costes de interrumpibilidad

**Uso**: Tarifa residencial más común en España.

### 600 - Precio Spot

Precio del mercado diario (day-ahead market).

**Uso**: Precio base del mercado mayorista.

### 1739 - PVPC Base

Precio base del PVPC antes de añadir cargos adicionales.

**Uso**: Análisis de componentes del precio final.

## Arquitectura de Recolección

### Componentes

1. **ESIOSClient** (`src/esios_client.py`)
   - Gestiona la comunicación con la API
   - Maneja autenticación
   - Implementa rate limiting
   - Procesa respuestas JSON

2. **PVPCDataCollector** (`src/data_collector.py`)
   - Orquesta la recolección de datos
   - Divide peticiones en chunks
   - Procesa y limpia datos
   - Guarda resultados en CSV

3. **CLI Script** (`collect_data.py`)
   - Interfaz de línea de comandos
   - Gestiona argumentos y configuración
   - Proporciona logging detallado

### Flujo de Datos

```
Usuario -> CLI Script -> PVPCDataCollector -> ESIOSClient -> API ESIOS
                              ↓
                        Procesamiento
                              ↓
                         Validación
                              ↓
                      Almacenamiento CSV
```

## Estrategia de Recolección

### División en Chunks

Para evitar límites de la API y timeouts:

- Peticiones divididas en chunks de 365 días
- Delay de 1 segundo entre peticiones
- Reintentos automáticos en caso de error

### Gestión de Errores

- Logging de todos los errores
- Continuación tras errores parciales
- Validación de respuestas

### Procesamiento de Datos

1. **Conversión de timestamps**: UTC a Europe/Madrid
2. **Eliminación de duplicados**: Mantener primer registro
3. **Ordenación**: Por fecha y hora
4. **Renombrado de columnas**: Para claridad

## Formato de Salida

### CSV

Archivos generados:

- `{indicator}_{start}_{end}.csv`: Datos del rango específico
- `{indicator}_latest.csv`: Última versión actualizada

### Columnas

- `datetime`: Timestamp (Europe/Madrid timezone)
- `price_eur_mwh`: Precio en EUR/MWh
- `indicator_id`: ID del indicador en ESIOS
- `indicator_name`: Nombre descriptivo del indicador

### Ejemplo

```csv
datetime,price_eur_mwh,indicator_id,indicator_name
2024-01-01 00:00:00+01:00,89.45,1001,PVPC 2.0TD
2024-01-01 01:00:00+01:00,87.32,1001,PVPC 2.0TD
...
```

## Casos de Uso

### Recolección Inicial

Obtener todo el histórico desde 2021:

```bash
python collect_data.py --start-date 2021-01-01 --indicator all
```

### Actualización Incremental

Obtener datos de la última semana:

```bash
python collect_data.py --start-date $(date -d '7 days ago' +%Y-%m-%d)
```

### Análisis Específico

Solo precio spot para análisis del mercado mayorista:

```bash
python collect_data.py --indicator pvpc_spot --start-date 2024-01-01
```

## Consideraciones

### Rate Limiting

La API de ESIOS tiene límites de peticiones:

- Implementamos delays entre peticiones
- División en chunks razonables
- Respeto de headers de rate limiting

### Calidad de Datos

- Algunos días pueden tener datos incompletos
- Cambios de horario (DST) pueden causar gaps
- Validar siempre la completitud de los datos

### Almacenamiento

- CSV es adecuado para datasets pequeños-medianos
- Para datasets grandes (varios años), considerar base de datos
- Compresión recomendada para archivos grandes

## Troubleshooting

### Error: No API Token

**Problema**: `No API token provided`

**Solución**:
1. Verificar que `.env` existe y contiene `ESIOS_API_TOKEN`
2. O pasar token con `--token`

### Error: 401 Unauthorized

**Problema**: Token inválido o expirado

**Solución**:
1. Verificar token en ESIOS dashboard
2. Generar nuevo token si es necesario

### Error: 429 Too Many Requests

**Problema**: Exceso de peticiones

**Solución**:
1. Aumentar delay entre peticiones
2. Reducir tamaño de chunks
3. Esperar antes de reintentar

### Datos Incompletos

**Problema**: Faltan horas en el dataset

**Solución**:
1. Verificar logs para errores específicos
2. Re-ejecutar recolección para períodos faltantes
3. Verificar disponibilidad en ESIOS web

## Referencias

- [ESIOS API Documentation](https://www.esios.ree.es/en)
- [PVPC Methodology](https://www.esios.ree.es/en/pvpc)
- [REE Official Website](https://www.ree.es)

## Próximas Mejoras

1. **Base de Datos**
   - Migrar a PostgreSQL/SQLite
   - Índices para consultas rápidas
   - Gestión de actualizaciones incrementales

2. **Validación Avanzada**
   - Detección de anomalías
   - Completitud de series temporales
   - Alertas automáticas

3. **Monitorización**
   - Dashboard de estado
   - Métricas de calidad
   - Alertas de fallos

4. **Automatización**
   - Cron jobs para actualización diaria
   - Retry automático con backoff exponencial
   - Notificaciones de éxito/fallo
