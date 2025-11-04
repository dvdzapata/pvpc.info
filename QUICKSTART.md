# Guía Rápida de Inicio

## 🚀 Inicio Rápido en 5 Minutos

### 1. Requisitos Previos

- Python 3.8 o superior
- Git
- Cuenta en ESIOS (gratuita)

### 2. Obtener Token de API

1. Ir a https://www.esios.ree.es/en
2. Crear una cuenta (si no tienes una)
3. Solicitar token de API:
   - Navegar a "API" en el menú
   - Solicitar un nuevo token
   - Guardar el token (lo necesitarás en el siguiente paso)

### 3. Instalación

```bash
# Clonar el repositorio
git clone https://github.com/dvdzapata/pvpc.info.git
cd pvpc.info

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar token
cp .env.example .env
# Editar .env y añadir tu token: ESIOS_API_TOKEN=tu_token_aqui
```

### 4. Primera Recolección de Datos

```bash
# Recolectar datos del último mes
python collect_data.py --start-date 2024-10-01

# Recolectar datos desde 2021
python collect_data.py --start-date 2021-01-01

# Recolectar todos los indicadores
python collect_data.py --indicator all --start-date 2023-01-01
```

### 5. Ver Resultados

Los datos se guardan en el directorio `data/`:

```bash
# Listar archivos generados
ls -lh data/

# Ver primeras líneas del archivo
head -20 data/pvpc_2.0TD_latest.csv

# Ver estadísticas
python -c "import pandas as pd; df = pd.read_csv('data/pvpc_2.0TD_latest.csv'); print(df.describe())"
```

## 📊 Análisis Básico con Python

```python
import pandas as pd
import matplotlib.pyplot as plt

# Leer datos
df = pd.read_csv('data/pvpc_2.0TD_latest.csv', 
                 index_col='datetime', 
                 parse_dates=True)

# Estadísticas básicas
print("Resumen de precios:")
print(f"Media: {df['price_eur_mwh'].mean():.2f} EUR/MWh")
print(f"Mínimo: {df['price_eur_mwh'].min():.2f} EUR/MWh")
print(f"Máximo: {df['price_eur_mwh'].max():.2f} EUR/MWh")

# Precio medio por hora del día
hourly = df.groupby(df.index.hour)['price_eur_mwh'].mean()
print("\nPrecio medio por hora:")
print(hourly)

# Visualizar evolución temporal
df['price_eur_mwh'].plot(figsize=(12, 6), 
                          title='Evolución PVPC')
plt.ylabel('EUR/MWh')
plt.tight_layout()
plt.savefig('pvpc_evolution.png')
print("\nGráfico guardado como 'pvpc_evolution.png'")

# Patrón diario promedio
hourly.plot(kind='bar', figsize=(10, 6),
            title='Precio Promedio por Hora del Día')
plt.xlabel('Hora del día')
plt.ylabel('EUR/MWh')
plt.tight_layout()
plt.savefig('pvpc_daily_pattern.png')
print("Gráfico guardado como 'pvpc_daily_pattern.png'")
```

## 🔄 Actualización Automática

### Cron Job (Linux/Mac)

Añadir a crontab para actualización diaria a las 2 AM:

```bash
# Editar crontab
crontab -e

# Añadir esta línea
0 2 * * * cd /ruta/a/pvpc.info && /ruta/a/venv/bin/python collect_data.py --start-date $(date -d '7 days ago' +\%Y-\%m-\%d) >> logs/cron.log 2>&1
```

### Task Scheduler (Windows)

1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Configurar:
   - Nombre: "PVPC Data Collection"
   - Desencadenador: Diariamente a las 2:00 AM
   - Acción: Iniciar programa
   - Programa: `C:\ruta\a\venv\Scripts\python.exe`
   - Argumentos: `collect_data.py --start-date 2024-01-01`
   - Directorio: `C:\ruta\a\pvpc.info`

## 📝 Opciones del CLI

```bash
# Ver todas las opciones
python collect_data.py --help

# Especificar rango de fechas
python collect_data.py --start-date 2024-01-01 --end-date 2024-12-31

# Indicador específico
python collect_data.py --indicator pvpc_spot

# Token directo (sin .env)
python collect_data.py --token TU_TOKEN_AQUI

# Modo verbose (más información)
python collect_data.py --verbose
```

## 🎯 Casos de Uso Comunes

### Análisis del Último Año

```bash
python collect_data.py --start-date 2023-01-01 --end-date 2023-12-31
```

### Solo Precio Spot (Mercado Mayorista)

```bash
python collect_data.py --indicator pvpc_spot --start-date 2024-01-01
```

### Actualización Incremental (Últimos 7 Días)

```bash
python collect_data.py --start-date $(date -d '7 days ago' +%Y-%m-%d)
```

### Histórico Completo (Desde 2021)

```bash
python collect_data.py --indicator all --start-date 2021-01-01 --verbose
```

## ❓ Solución de Problemas

### Error: No API Token

```
Error: No API token provided
```

**Solución**: 
1. Verificar que `.env` existe
2. Verificar que contiene `ESIOS_API_TOKEN=tu_token`
3. O usar `--token TU_TOKEN` en la línea de comandos

### Error: 401 Unauthorized

```
Error: 401 Client Error: Unauthorized
```

**Solución**: Token inválido o expirado. Generar nuevo token en ESIOS.

### Error: Connection Timeout

```
Error: Connection timeout
```

**Solución**: 
1. Verificar conexión a internet
2. Reducir rango de fechas
3. Aumentar timeout en el código

### Datos Incompletos

Si faltan horas en el dataset:

1. Verificar logs: `cat logs/data_collection.log`
2. Re-ejecutar para el período específico
3. Verificar disponibilidad en https://www.esios.ree.es

## 📚 Más Información

- **Documentación completa**: Ver `docs/DATA_COLLECTION.md`
- **Ejemplos de salida**: Ver `docs/SAMPLE_OUTPUT.md`
- **README principal**: Ver `README.md`

## 🤝 Soporte

- Issues: https://github.com/dvdzapata/pvpc.info/issues
- Email: (por definir)
- Documentación ESIOS: https://www.esios.ree.es/en

## 🎉 ¡Listo!

Ya estás recolectando datos históricos de precios PVPC. El siguiente paso es:

1. **Análisis de datos**: Usar Python/R para análisis estadístico
2. **Desarrollo de API**: Exponer datos vía REST API
3. **Predicción**: Entrenar modelo TFT para forecasting
4. **Visualización**: Crear dashboards interactivos

¡Buena suerte con tu proyecto!
