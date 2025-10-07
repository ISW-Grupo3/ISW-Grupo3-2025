# Sistema de Compra de Entradas - Parque

## Descripción
Sistema de gestión de compra de entradas para un parque temático, desarrollado usando **TDD (Test-Driven Development)** con persistencia en **SQLite**.

## Características Principales

### Historia de Usuario Implementada
**COMO** visitante **QUIERO** comprar una entrada **PARA** asegurar mi visita al parque

### Criterios de Aceptación ✅
- ✅ Indicar fecha de visita, cantidad de entradas, edad de visitantes y tipo de pase
- ✅ Fecha de visita puede ser del día actual o futura
- ✅ Envía mensaje de confirmación vía mail (simulado)
- ✅ Redirige a Mercado Pago para pagos con tarjeta (simulado)
- ✅ Validación de días de apertura del parque
- ✅ Selección de forma de pago (efectivo o tarjeta)
- ✅ Límite máximo de 10 entradas por compra
- ✅ Información de cantidad y fecha al finalizar
- ✅ Solo usuarios registrados pueden comprar

### Pruebas de Usuario Implementadas
- ✅ Compra exitosa con todos los datos válidos
- ✅ Fallo sin seleccionar forma de pago
- ✅ Fallo en fechas cuando el parque está cerrado
- ✅ Fallo al exceder límite de 10 entradas

## Estructura del Proyecto

```
ISW_TPE_06_TDD/
├── src/
│   ├── __init__.py
│   ├── gestor_entradas.py    # Lógica principal de negocio
│   └── database.py           # Gestión de persistencia SQLite
├── tests/
│   ├── __init__.py
│   ├── test_gestor_entradas.py     # Tests originales
│   └── test_gestor_entradas_db.py  # Tests con persistencia
├── demo.py                   # Script de demostración
├── requirements.txt          # Dependencias
└── README.md                # Este archivo
```

## Base de Datos

### Esquema SQLite

**Tablas principales:**
- `usuarios`: Gestión de usuarios registrados
- `compras`: Registro de compras de entradas
- `visitantes`: Detalles de cada visitante por compra
- `configuracion_parque`: Configuración del parque (capacidad, precios)
- `dias_cerrados`: Días en que el parque está cerrado

## Instalación y Configuración

### 1. Configurar Entorno Virtual
```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Actualizar pip
python.exe -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar Tests
```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Ejecutar todos los tests
pytest

# Tests con detalle
pytest -v

# Tests específicos de base de datos
pytest tests/test_gestor_entradas_db.py -v

# Test específico
pytest tests/test_gestor_entradas_db.py::test_compra_exitosa_y_retorna_datos -v
```

### 3. Ejecutar Demostración
```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Ejecutar script de demostración
python demo.py
```

## Uso del Sistema

### Ejemplo Básico
```python
from src.gestor_entradas import GestorDeEntradas
from datetime import date, timedelta

# Inicializar gestor
gestor = GestorDeEntradas()

# Registrar usuario
usuario_id = gestor.registrar_usuario("usuario@email.com", "Juan Pérez")

# Comprar entradas
resultado = gestor.comprar_entradas(
    fecha_visita=date.today() + timedelta(days=10),
    cantidad=2,
    detalles_visitantes=[
        {"nombre": "Ana", "edad": 25},
        {"nombre": "Luis", "edad": 30}
    ],
    tipo_pase="VIP",
    forma_pago="tarjeta",
    usuario_email="usuario@email.com"
)

print(f"Compra ID: {resultado['compra_id']}")
```

### Tipos de Pases
- **Regular**: Pase estándar
- **VIP**: Pase premium con beneficios adicionales  
- **Estudiante**: Pase con descuento para estudiantes

### Formas de Pago
- **efectivo**: Pago en boletería
- **tarjeta**: Pago online con redirección a Mercado Pago

## Validaciones Implementadas

### Criterios de Aceptación (CA)
- Usuario debe estar registrado
- Cantidad máxima: 10 entradas por compra
- Fecha no puede ser en el pasado
- Parque cerrado en fechas específicas (Navidad, Año Nuevo)
- Forma de pago obligatoria
- Datos de visitantes completos y válidos
- Capacidad máxima del parque (100 personas/día)

### Manejo de Errores
- `PermissionError`: Usuario no registrado
- `ValueError`: Datos inválidos (cantidad, fecha, edad, etc.)

## Funcionalidades Adicionales

### Gestión de Capacidad
- Control automático de capacidad máxima por fecha
- Consulta de disponibilidad en tiempo real
- Prevención de sobreventa

### Persistencia de Datos
- Todas las compras se guardan en SQLite
- Historial completo de transacciones
- Gestión de usuarios registrados
- Configuración flexible del parque

### Confirmaciones
- Email de confirmación (simulado)
- Integración con Mercado Pago (simulado)
- Estados de pago rastreables

## Arquitectura

### Principios Aplicados
- **TDD**: Tests escritos antes que el código
- **Single Responsibility**: Cada clase tiene una responsabilidad clara
- **Separation of Concerns**: Lógica de negocio separada de persistencia
- **Database Abstraction**: Capa de abstracción para SQLite

### Patrones de Diseño
- **Repository Pattern**: DatabaseManager como capa de acceso a datos
- **Factory Pattern**: Creación de compras y usuarios
- **Strategy Pattern**: Diferentes formas de pago

## Comandos Útiles

```powershell
# Tests específicos
pytest tests/test_gestor_entradas_db.py::test_flujo_completo_compra_exitosa -v

# Coverage de tests
pytest --cov=src tests/

# Ejecutar solo tests que fallan
pytest tests/test_gestor_entradas_db.py -k "falla" -v

# Ejecutar solo tests exitosos
pytest tests/test_gestor_entradas_db.py -k "exitosa" -v
```

## Base de Datos

La base de datos `parque_entradas.db` se crea automáticamente con:
- Datos iniciales de configuración
- Días cerrados por defecto
- Estructura de tablas completa

**Inspeccionar BD:**
```bash
sqlite3 parque_entradas.db
.tables
.schema compras
SELECT * FROM compras;
```

---

## Desarrollo

Este proyecto implementa TDD, por lo que:
1. **Tests primero**: Criterios de aceptación → Tests → Código
2. **Refactoring continuo**: Mejorar código manteniendo tests verdes
3. **Cobertura completa**: Todos los criterios tienen tests asociados
