# Guía de Contribución

¡Gracias por tu interés en contribuir a pvpc.info! Este documento proporciona las pautas para contribuir al proyecto.

## 🌟 Cómo Contribuir

### Reportar Bugs

Si encuentras un bug:

1. Verifica que no exista ya un issue similar
2. Crea un nuevo issue con:
   - Título descriptivo
   - Descripción detallada del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Versión de Python y sistema operativo
   - Logs relevantes

### Sugerir Mejoras

Para sugerir nuevas características:

1. Verifica que no exista ya una sugerencia similar
2. Crea un issue con:
   - Título claro de la funcionalidad
   - Caso de uso detallado
   - Beneficios de la implementación
   - Posible implementación (opcional)

### Pull Requests

1. **Fork** el repositorio
2. **Crea una rama** desde `main`:
   ```bash
   git checkout -b feature/mi-nueva-funcionalidad
   ```
3. **Realiza tus cambios**:
   - Sigue el estilo de código existente
   - Añade tests para nuevas funcionalidades
   - Actualiza la documentación si es necesario
4. **Commit** tus cambios:
   ```bash
   git commit -m "feat: añadir nueva funcionalidad X"
   ```
5. **Push** a tu fork:
   ```bash
   git push origin feature/mi-nueva-funcionalidad
   ```
6. **Crea un Pull Request** en GitHub

## 📝 Estilo de Código

### Python

- Seguir [PEP 8](https://pep8.org/)
- Usar docstrings para funciones y clases
- Nombres descriptivos para variables y funciones
- Máximo 100 caracteres por línea

Ejemplo:

```python
def fetch_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch PVPC data for a date range
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        DataFrame with PVPC prices
    """
    # Implementation
    pass
```

### Commits

Usar [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Cambios de formato (sin cambios funcionales)
- `refactor:` Refactorización de código
- `test:` Añadir o modificar tests
- `chore:` Tareas de mantenimiento

Ejemplos:
```
feat: añadir soporte para PostgreSQL
fix: corregir timezone en datos históricos
docs: actualizar README con nuevos ejemplos
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_esios_client.py

# Con coverage
pytest --cov=src tests/
```

### Escribir Tests

- Un test por funcionalidad
- Nombres descriptivos
- Usar mocks para APIs externas
- Cubrir casos edge

Ejemplo:

```python
def test_data_collector_handles_empty_response():
    """Test that collector handles empty API response gracefully"""
    # Setup
    collector = PVPCDataCollector()
    
    # Test
    with patch('src.esios_client.ESIOSClient.get_indicator_data') as mock:
        mock.return_value = pd.DataFrame()
        result = collector.collect_historical_data('2024-01-01', '2024-01-02')
    
    # Assert
    assert result.empty
```

## 📚 Documentación

### Actualizar Documentación

Si tu cambio afecta:

- **README.md**: Actualizar si cambia la funcionalidad principal
- **docs/**: Actualizar guías detalladas
- **Docstrings**: Mantener actualizados en el código
- **QUICKSTART.md**: Actualizar si cambia el uso básico

### Escribir Documentación

- Clara y concisa
- Con ejemplos prácticos
- En español (documentación de usuario)
- Docstrings en inglés (código)

## 🔍 Revisión de Código

Los Pull Requests serán revisados considerando:

1. **Funcionalidad**: ¿Resuelve el problema?
2. **Tests**: ¿Tiene tests adecuados?
3. **Documentación**: ¿Está documentado?
4. **Estilo**: ¿Sigue las guías de estilo?
5. **Rendimiento**: ¿Es eficiente?

## 🎯 Áreas de Contribución

### Prioridad Alta

- Soporte para base de datos (PostgreSQL, SQLite)
- API REST pública
- Tests adicionales
- Documentación en inglés
- CI/CD pipeline

### Prioridad Media

- Visualizaciones interactivas
- Dashboard web
- Integración con otras fuentes de datos
- Optimizaciones de rendimiento
- Docker support

### Prioridad Baja

- Aplicación móvil
- Alertas de precios
- Exportación a formatos adicionales
- Internacionalización

## 🚀 Desarrollo Local

### Setup

```bash
# Clonar
git clone https://github.com/dvdzapata/pvpc.info.git
cd pvpc.info

# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar dependencias de desarrollo (futuro)
# pip install -r requirements-dev.txt
```

### Estructura del Proyecto

```
pvpc.info/
├── src/              # Código fuente
│   ├── esios_client.py
│   ├── data_collector.py
│   └── config.py
├── tests/            # Tests
├── docs/             # Documentación
├── data/             # Datos (ignorado en git)
└── logs/             # Logs (ignorado en git)
```

### Workflow

1. Crear issue para discutir cambio
2. Crear rama desde `main`
3. Implementar cambio
4. Añadir tests
5. Actualizar docs
6. Push y crear PR
7. Responder a comentarios de revisión
8. Merge cuando sea aprobado

## 📞 Contacto

- **Issues**: Para bugs y sugerencias
- **Discussions**: Para preguntas y discusiones
- **Email**: (por definir)

## 📜 Código de Conducta

### Nuestro Compromiso

Nos comprometemos a hacer de este proyecto una experiencia libre de acoso para todos, independientemente de:

- Edad
- Tamaño corporal
- Discapacidad
- Etnicidad
- Identidad y expresión de género
- Nivel de experiencia
- Nacionalidad
- Apariencia personal
- Raza
- Religión
- Identidad y orientación sexual

### Comportamiento Esperado

- Usar lenguaje acogedor e inclusivo
- Respetar diferentes puntos de vista
- Aceptar crítica constructiva
- Enfocarse en lo mejor para la comunidad
- Mostrar empatía hacia otros miembros

### Comportamiento Inaceptable

- Lenguaje o imágenes sexualizadas
- Trolling o comentarios insultantes
- Acoso público o privado
- Publicar información privada de otros
- Conducta que sea inapropiada profesionalmente

## 🙏 Agradecimientos

¡Gracias por contribuir a pvpc.info! Cada contribución, por pequeña que sea, es valiosa y ayuda a mejorar el proyecto.

---

**Nota**: Esta guía está en desarrollo. Sugerencias de mejora son bienvenidas.
