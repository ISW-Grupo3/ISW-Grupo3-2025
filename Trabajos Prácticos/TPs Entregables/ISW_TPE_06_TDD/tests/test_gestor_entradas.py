import pytest
from datetime import date, timedelta
from src.gestor_entradas import GestorDeEntradas
import builtins
from unittest import mock

HOY = date.today()
AYER = HOY - timedelta(days=1)
FECHA_FUTURA = HOY + timedelta(days=30) 
FECHA_CERRADA = date(2025, 12, 25)

VISITANTE_VALIDO = [{"nombre": "Juan", "edad": 30}]
VISITANTES_VALIDOS = [{"nombre": "Ana", "edad": 25}, {"nombre": "Luis", "edad": 15}]


@pytest.fixture
def gestor():
    return GestorDeEntradas()

# --- TESTS DE CA (FALLAN) ---

def test_compra_falla_si_usuario_no_esta_registrado(gestor):
    """Criterio: Solo usuarios registrados pueden comprar."""
    with pytest.raises(PermissionError):
        gestor.comprar_entradas(FECHA_FUTURA, 1, VISITANTE_VALIDO, "Regular", "efectivo", usuario_registrado=False)

def test_compra_falla_si_cantidad_es_mayor_a_diez(gestor):
    """Criterio: Cantidad máxima de 10 entradas."""
    with pytest.raises(ValueError, match="un número entre 1 y 10"):
        gestor.comprar_entradas(FECHA_FUTURA, 11, [], "VIP", "tarjeta", usuario_registrado=True)

def test_compra_falla_si_parque_cerrado(gestor):
    """Prueba de usuario: Fecha en día cerrado."""
    with pytest.raises(ValueError, match="El parque se encuentra cerrado"):
        gestor.comprar_entradas(FECHA_CERRADA, 1, VISITANTE_VALIDO, "Regular", "tarjeta", usuario_registrado=True)
        
def test_compra_falla_si_fecha_es_pasada(gestor):
    """Criterio: La fecha de visita no puede ser pasada."""
    with pytest.raises(ValueError, match="no puede ser una fecha pasada"):
        gestor.comprar_entradas(AYER, 1, VISITANTE_VALIDO, "Regular", "tarjeta", usuario_registrado=True)

def test_compra_falla_sin_forma_de_pago(gestor):
    """Prueba de usuario: Sin forma de pago."""
    with pytest.raises(ValueError, match="Debe seleccionar una forma de pago"):
        gestor.comprar_entradas(FECHA_FUTURA, 1, VISITANTE_VALIDO, "Regular", "", usuario_registrado=True)

def test_compra_falla_si_detalles_no_coinciden_con_cantidad(gestor):
    """Criterio: La cantidad de entradas debe coincidir con la lista de visitantes."""
    with pytest.raises(ValueError, match="no coincide con la cantidad"):
        # Se piden 2 entradas, pero solo se envía 1 detalle de visitante
        gestor.comprar_entradas(FECHA_FUTURA, 2, VISITANTE_VALIDO, "Regular", "tarjeta", usuario_registrado=True)

def test_compra_falla_si_edad_es_negativa(gestor):
    """Criterio: La edad no puede ser menor a 0."""
    visitante_invalido = [{'nombre': 'Pepe', 'edad': -5}]
    with pytest.raises(ValueError, match="no puede ser negativa"):
        gestor.comprar_entradas(FECHA_FUTURA, 1, visitante_invalido, "Regular", "tarjeta", usuario_registrado=True)

def test_compra_falla_si_tipo_pase_es_invalido(gestor):
    """Criterio: El tipo de pase debe ser válido."""
    with pytest.raises(ValueError, match="no es válido"):
        gestor.comprar_entradas(FECHA_FUTURA, 1, VISITANTE_VALIDO, "Ultra-VIP-X", "tarjeta", usuario_registrado=True)

# --- TESTS DE CA (PASAN) ---

def test_compra_exitosa_y_retorna_datos(gestor):
    """Prueba de usuario: Compra exitosa (pasa)."""
    
    # Mockeamos el método interno de envío de mail para asegurar que se llama
    with mock.patch.object(gestor, '_enviar_mail_confirmacion') as mock_email:
        
        resultado = gestor.comprar_entradas(FECHA_FUTURA, 2, VISITANTES_VALIDOS, "Estudiante", "efectivo", usuario_registrado=True)
        
        # Criterio: Al finalizar la compra se debe informar la cantidad de entradas...
        assert resultado["mensaje"] == "Compra realizada con éxito"
        assert resultado["cantidad_entradas"] == 2
        assert resultado["fecha_visita"] == FECHA_FUTURA.strftime("%Y-%m-%d")
        
        # Criterio: Debe enviar un mensaje de confirmación vía mail.
        mock_email.assert_called_once()


def test_compra_con_tarjeta_simula_redireccion_a_pasarela(gestor):
    """Criterio: Si el pago es con tarjeta, redirigir a mercado pago (simulación)."""
    
    # Mockeamos el método de pago para verificar que la simulación de tarjeta se ejecuta
    with mock.patch.object(gestor, '_procesar_pago', return_value=True) as mock_pago:
        
        gestor.comprar_entradas(FECHA_FUTURA, 1, VISITANTE_VALIDO, "VIP", "tarjeta", usuario_registrado=True)
        
        # Verificamos que se llamó a procesar pago con 'tarjeta'
        mock_pago.assert_called_once_with("tarjeta")
        