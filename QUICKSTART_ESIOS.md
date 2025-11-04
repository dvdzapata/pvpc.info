# 🚀 Inicio Rápido - ESIOS Data Collection

## Para el Usuario No Programador

Este script es **fácil de usar** y **no requiere mantenimiento**. Sigue estos pasos:

### Paso 1: Preparación (Solo una vez)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Obtener token de API ESIOS (gratis)
# Visita: https://www.esios.ree.es/en
# Registra cuenta → Solicita API token

# 3. Configurar token
cp .env.example .env
nano .env  # o usa tu editor favorito
# Añade tu token: ESIOS_API_TOKEN=tu_token_aqui
```

### Paso 2: Primera Ejecución

```bash
# Ver qué indicadores hay disponibles (no descarga datos)
python3 process_esios_indicators.py --catalog-only

# Esto crea: indicators-pack1.json
# Mira este archivo para ver los 1960 indicadores disponibles
```

### Paso 3: Configurar PostgreSQL (Solo una vez)

```bash
# Opción A: PostgreSQL local ya instalado
sudo -u postgres createdb esios_data

# Opción B: PostgreSQL en Docker
docker run --name postgres-esios \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=esios_data \
  -p 5432:5432 \
  -d postgres:16

# Inicializar tablas
python3 process_esios_indicators.py --init-db
```

### Paso 4: Descargar Datos

```bash
# Descargar datos prioritarios del último año
# Esto puede tardar varias horas - es normal
python3 process_esios_indicators.py \
    --start-date 2024-01-01 \
    --priority 2

# El script muestra una barra de progreso
# Puedes cerrar (Ctrl+C) y continuar después con --resume
```

### Paso 5: Automatizar Actualizaciones Diarias

```bash
# Hacer ejecutable el script de actualización diaria
chmod +x daily_update.sh

# Añadir a crontab (ejecuta todos los días a la 1 AM)
crontab -e
# Añadir esta línea (ajusta la ruta):
0 1 * * * /ruta/completa/a/pvpc.info/daily_update.sh >> /var/log/esios.log 2>&1
```

## 🎯 Casos de Uso Comunes

### Ver qué indicadores hay
```bash
python3 process_esios_indicators.py --catalog-only
# Revisa indicators-pack1.json
```

### Descargar solo precios y demanda (lo más rápido)
```bash
python3 process_esios_indicators.py \
    --start-date 2024-01-01 \
    --priority 1
# Solo 80 indicadores, ~2-3 horas
```

### Descargar datos completos para predicción
```bash
python3 process_esios_indicators.py \
    --start-date 2024-01-01 \
    --priority 3
# 193 indicadores, ~5-6 horas
```

### Actualizar datos de ayer
```bash
python3 process_esios_indicators.py --daily-update
# 30-60 minutos
```

### Continuar descarga interrumpida
```bash
# Si se interrumpió, simplemente añade --resume
python3 process_esios_indicators.py \
    --start-date 2024-01-01 \
    --priority 2 \
    --resume
```

## 📊 Verificar que Todo Funciona

```bash
# 1. Ver logs
tail -f logs/esios_*.log

# 2. Consultar base de datos
psql -d esios_data -c "SELECT COUNT(*) FROM indicators;"
psql -d esios_data -c "SELECT COUNT(*) FROM indicator_values;"

# 3. Ver últimas recolecciones
psql -d esios_data -c "
SELECT 
    indicator_id,
    status,
    records_fetched,
    created_at
FROM data_collection_logs
ORDER BY created_at DESC
LIMIT 10;
"
```

## ❓ Problemas Comunes

### "No API token provided"
**Solución**: Edita el archivo `.env` y añade tu token:
```bash
echo "ESIOS_API_TOKEN=tu_token_aqui" >> .env
```

### "Database connection failed"
**Solución**: Verifica que PostgreSQL está corriendo:
```bash
# Ver estado
sudo systemctl status postgresql

# Si no está corriendo, iniciar
sudo systemctl start postgresql
```

### Se interrumpió la descarga
**No hay problema**. Simplemente ejecuta de nuevo con `--resume`:
```bash
python3 process_esios_indicators.py --start-date 2024-01-01 --resume
```

### Va muy lento
**Es normal**. El sistema respeta límites de la API:
- 50 peticiones por minuto
- Descarga completa: ~16 horas
- Actualización diaria: ~30-60 minutos

### Error "JSON decode error"
**El script lo maneja automáticamente**. No requiere acción.

## 📞 Soporte

1. **Revisar logs**: `tail -50 logs/esios_*.log`
2. **Ver documentación**: `README_ESIOS_SCRIPT.md`
3. **Documentación técnica**: `docs/ESIOS_DATA_COLLECTION.md`
4. **Abrir issue**: GitHub con extracto del log

## 🎓 Próximos Pasos

Una vez tienes datos en PostgreSQL:

1. **Analizar datos**: Usa queries SQL o pandas
2. **Desarrollar modelo TFT**: Para predicción de precios
3. **Crear API**: Exponer datos vía REST API
4. **Desarrollar frontend**: Visualizar datos y predicciones

## 💡 Consejos

- **Empieza con `--catalog-only`**: Para ver qué hay disponible
- **Usa `--priority 1`** primero: Descarga lo esencial rápidamente
- **Monitorea logs**: Para ver progreso en tiempo real
- **Usa `--resume`** siempre: Evita re-descargar datos
- **Automatiza actualizaciones**: Con cron para mantener datos actualizados

## ✅ Checklist de Éxito

- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Token ESIOS configurado en `.env`
- [ ] PostgreSQL corriendo y base de datos creada
- [ ] Tablas inicializadas (`--init-db`)
- [ ] Catálogo generado (`--catalog-only`)
- [ ] Primera descarga completada (`--start-date 2024-01-01`)
- [ ] Actualización diaria configurada (crontab)
- [ ] Datos verificados (queries SQL)

---

**¿Listo para empezar?** Ejecuta:
```bash
python3 process_esios_indicators.py --catalog-only
```
