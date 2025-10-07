import pytest
import os
from datetime import date, timedelta
from src.gestor_entradas import GestorDeEntradas
from src.database import DatabaseManager
from unittest import mock

# Constantes para tests
HOY = date.today()
AYER = HOY - timedelta(days=1)
FECHA_FUTURA = HOY + timedelta(days=30) 
FECHA_CERRADA = date(2025, 12, 25)

VISITANTE_VALIDO = [{"nombre": "Juan", "edad": 30}]
VISITANTES_VALIDOS = [{"nombre": "Ana", "edad": 25}, {"nombre": "Luis", "edad": 15}]

# Email de usuario de prueba
EMAIL_USUARIO_VALIDO = "test@example.com"
EMAIL_USUARIO_INVALIDO = "noexiste@example.com"

@pytest.fixture
def db_test():
    """Crea una base de datos de prueba temporal"""
    db_path = "test_parque.db"
    db = DatabaseManager(db_path)
    # Registrar usuario de prueba
    db.registrar_usuario(EMAIL_USUARIO_VALIDO, "Usuario Test")
    yield db
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def gestor(db_test):
    """Crea un gestor con base de datos de prueba"""
    return GestorDeEntradas("test_parque.db")

# --- TESTS DE CA (FALLAN) ---

def test_compra_falla_si_usuario_no_esta_registrado(gestor):
    """Criterio: Solo usuarios registrados pueden comprar."""
    with pytest.raises(PermissionError, match="usuarios registrados"):
        gestor.comprar_entradas(
            FECHA_FUTURA, 1, VISITANTE_VALIDO, "Regular", "efectivo", 
            EMAIL_USUARIO_INVALIDO
        )

def test_compra_falla_si_cantidad_es_mayor_a_diez(gestor):
    """Criterio: Cantidad máxima de 10 entradas."""
    with pytest.raises(ValueError, match="un número entre 1 y 10"):
        gestor.comprar_entradas(
            FECHA_FUTURA, 11, [], "VIP", "tarjeta", 
            EMAIL_USUARIO_VALIDO
        )

def test_compra_falla_si_parque_cerrado(gestor):
    """Prueba de usuario: Fecha en día cerrado."""
    with pytest.raises(ValueError, match="El parque se encuentra cerrado"):
        gestor.comprar_entradas(
            FECHA_CERRADA, 1, VISITANTE_VALIDO, "Regular", "tarjeta", 
            EMAIL_USUARIO_VALIDO
        )
        
def test_compra_falla_si_fecha_es_pasada(gestor):
    """Criterio: La fecha de visita no puede ser pasada."""
    with pytest.raises(ValueError, match="no puede ser en el pasado"):
        gestor.comprar_entradas(
            AYER, 1, VISITANTE_VALIDO, "Regular", "tarjeta", 
            EMAIL_USUARIO_VALIDO
        )

def test_compra_falla_sin_forma_de_pago(gestor):
    """Prueba de usuario: Sin forma de pago."""
    with pytest.raises(ValueError, match="Debe seleccionar una forma de pago"):
        gestor.comprar_entradas(
            FECHA_FUTURA, 1, VISITANTE_VALIDO, "Regular", "", 
            EMAIL_USUARIO_VALIDO
        )

def test_compra_falla_si_detalles_no_coinciden_con_cantidad(gestor):
    """Criterio: La cantidad de entradas debe coincidir con la lista de visitantes."""
    with pytest.raises(ValueError, match="no coincide con la cantidad"):
        # Se piden 2 entradas, pero solo se envía 1 detalle de visitante
        gestor.comprar_entradas(
            FECHA_FUTURA, 2, VISITANTE_VALIDO, "Regular", "tarjeta", 
            EMAIL_USUARIO_VALIDO
        )

def test_compra_falla_si_edad_es_negativa(gestor):
    """Criterio: La edad no puede ser menor a 0."""
    visitante_invalido = [{'nombre': 'Pepe', 'edad': -5}]
    with pytest.raises(ValueError, match="número positivo"):
        gestor.comprar_entradas(
            FECHA_FUTURA, 1, visitante_invalido, "Regular", "tarjeta", 
            EMAIL_USUARIO_VALIDO
        )

def test_compra_falla_si_tipo_pase_es_invalido(gestor):
    """Criterio: El tipo de pase debe ser válido."""
    with pytest.raises(ValueError, match="no es válido"):
        gestor.comprar_entradas(
            FECHA_FUTURA, 1, VISITANTE_VALIDO, "Ultra-VIP-X", "tarjeta", 
            EMAIL_USUARIO_VALIDO
        )

def test_compra_falla_si_excede_capacidad(gestor):
    """Criterio: No se puede exceder la capacidad máxima del parque."""
    # Primero llenar casi toda la capacidad
    for i in range(10):  # 10 compras de 10 entradas cada una = 100 entradas
        gestor.comprar_entradas(
            FECHA_FUTURA, 10, 
            [{"nombre": f"Visitante{j}", "edad": 25} for j in range(10)], 
            "Regular", "efectivo", EMAIL_USUARIO_VALIDO
        )
    
    # Ahora intentar comprar una más debería fallar
    with pytest.raises(ValueError, match="Solo quedan 0 entradas disponibles"):
        gestor.comprar_entradas(
            FECHA_FUTURA, 1, VISITANTE_VALIDO, "Regular", "tarjeta", 
            EMAIL_USUARIO_VALIDO
        )

# --- TESTS DE CA (PASAN) ---

def test_compra_exitosa_y_retorna_datos(gestor):
    """Prueba de usuario: Compra exitosa (pasa)."""
    
    resultado = gestor.comprar_entradas(
        FECHA_FUTURA, 2, VISITANTES_VALIDOS, "Estudiante", "efectivo", 
        EMAIL_USUARIO_VALIDO
    )
    
    # Criterio: Al finalizar la compra se debe informar la cantidad de entradas...
    assert resultado["mensaje"] == "Compra realizada con éxito"
    assert resultado["cantidad_entradas"] == 2
    assert resultado["fecha_visita"] == FECHA_FUTURA.strftime("%Y-%m-%d")
    assert "compra_id" in resultado
    
    # Verificar que se guardó en la base de datos
    compra = gestor.obtener_compra(resultado["compra_id"])
    assert compra is not None
    assert compra["cantidad_entradas"] == 2
    assert compra["tipo_pase"] == "Estudiante"
    assert len(compra["visitantes"]) == 2

def test_compra_con_tarjeta_simula_redireccion_a_pasarela(gestor):
    """Criterio: Si el pago es con tarjeta, redirigir a mercado pago (simulación)."""
    
    # Capturar la salida del print para verificar la redirección
    with mock.patch('builtins.print') as mock_print:
        resultado = gestor.comprar_entradas(
            FECHA_FUTURA, 1, VISITANTE_VALIDO, "VIP", "tarjeta", 
            EMAIL_USUARIO_VALIDO
        )
        
        # Verificar que se mencionó Mercado Pago
        calls = [str(call) for call in mock_print.call_args_list]
        mercado_pago_mentioned = any("Mercado Pago" in call for call in calls)
        assert mercado_pago_mentioned, "Debería mencionar Mercado Pago para pagos con tarjeta"

def test_confirmacion_email_se_envia(gestor):
    """Criterio: Debe enviar un mensaje de confirmación vía mail."""
    
    with mock.patch('builtins.print') as mock_print:
        resultado = gestor.comprar_entradas(
            FECHA_FUTURA, 1, VISITANTE_VALIDO, "Regular", "efectivo", 
            EMAIL_USUARIO_VALIDO
        )
        
        # Verificar que se mencionó el envío de confirmación
        calls = [str(call) for call in mock_print.call_args_list]
        email_mentioned = any("confirmación" in call for call in calls)
        assert email_mentioned, "Debería enviar confirmación por email"
        
        # Verificar que se marcó como enviada en la BD
        compra = gestor.obtener_compra(resultado["compra_id"])
        assert compra["confirmacion_enviada"] == 1

def test_registro_de_nuevo_usuario(gestor):
    """Test adicional: Registro de nuevos usuarios."""
    nuevo_email = "nuevo@example.com"
    usuario_id = gestor.registrar_usuario(nuevo_email, "Usuario Nuevo")
    
    assert usuario_id > 0
    assert gestor.db.usuario_registrado(nuevo_email)

def test_consulta_disponibilidad(gestor):
    """Test adicional: Consultar disponibilidad de entradas."""
    # Al inicio debería haber capacidad máxima disponible
    disponibles = gestor.obtener_disponibilidad(FECHA_FUTURA)
    assert disponibles == 100
    
    # Después de una compra, debería reducirse
    gestor.comprar_entradas(
        FECHA_FUTURA, 5, 
        [{"nombre": f"Visitante{i}", "edad": 25} for i in range(5)], 
        "Regular", "efectivo", EMAIL_USUARIO_VALIDO
    )
    
    disponibles = gestor.obtener_disponibilidad(FECHA_FUTURA)
    assert disponibles == 95

# --- TESTS DE INTEGRACIÓN ---

def test_flujo_completo_compra_exitosa(gestor):
    """Test de integración: Flujo completo de compra exitosa."""
    
    # 1. Verificar que el usuario está registrado
    assert gestor.db.usuario_registrado(EMAIL_USUARIO_VALIDO)
    
    # 2. Realizar compra
    resultado = gestor.comprar_entradas(
        FECHA_FUTURA, 3,
        [
            {"nombre": "Ana García", "edad": 28},
            {"nombre": "Luis Pérez", "edad": 35},
            {"nombre": "María López", "edad": 22}
        ],
        "VIP", "tarjeta", EMAIL_USUARIO_VALIDO
    )
    
    # 3. Verificar resultado
    assert resultado["mensaje"] == "Compra realizada con éxito"
    compra_id = resultado["compra_id"]
    
    # 4. Verificar persistencia
    compra = gestor.obtener_compra(compra_id)
    assert compra["cantidad_entradas"] == 3
    assert compra["tipo_pase"] == "VIP"
    assert compra["forma_pago"] == "tarjeta"
    assert len(compra["visitantes"]) == 3
    
    # 5. Verificar capacidad actualizada
    disponibles = gestor.obtener_disponibilidad(FECHA_FUTURA)
    assert disponibles == 97
