from datetime import date
from .database import DatabaseManager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GestorDeEntradas:

    PASES_VALIDOS = ["Regular", "VIP"]
    
    def __init__(self, db_path: str = "parque_entradas.db"):
        self.db = DatabaseManager(db_path)
        # Cargar configuración desde la base de datos
        config = self.db.obtener_configuracion_parque()
        self.CAPACIDAD_MAXIMA = config.get('capacidad_maxima', 100)
        
    @property
    def DIAS_PARQUE_CERRADO(self):
        """Obtiene los días cerrados desde la base de datos"""
        dias_str = self.db.obtener_dias_cerrados()
        return [date.fromisoformat(dia) for dia in dias_str]

    def comprar_entradas(self, fecha_visita: date, cantidad: int, detalles_visitantes: list, 
                        tipo_pase: str, forma_pago: str, usuario_email: str) -> dict:
        # Validaciones
        self._validar_usuario(usuario_email)
        self._validar_cantidad(cantidad)
        self._validar_fecha(fecha_visita)
        self._validar_forma_pago(forma_pago)
        self.validar_capacidad(fecha_visita, cantidad)
        self._validar_detalles_visitantes(cantidad, detalles_visitantes, tipo_pase)

        # Procesar pago
        self._procesar_pago(forma_pago)

        # Crear compra en la base de datos
        compra_id = self.db.crear_compra(
            usuario_email=usuario_email,
            fecha_visita=fecha_visita.strftime("%Y-%m-%d"),
            cantidad=cantidad,
            visitantes=detalles_visitantes,
            tipo_pase=tipo_pase,
            forma_pago=forma_pago
        )

        # Enviar confirmación
        self._enviar_mail_confirmacion({
            "compra_id": compra_id,
            "cantidad": cantidad, 
            "fecha": fecha_visita,
            "usuario_email": usuario_email
        })
        
        # Marcar confirmación como enviada
        self.db.marcar_confirmacion_enviada(compra_id)

        return {
            "mensaje": "Compra realizada con éxito",
            "compra_id": compra_id,
            "cantidad_entradas": cantidad,
            "fecha_visita": fecha_visita.strftime("%Y-%m-%d")
        }

    def _validar_usuario(self, usuario_email: str):
        # CA: se debe permitir la compra de entradas solo a usuarios registrados.
        if not usuario_email or not self.db.usuario_registrado(usuario_email):
            raise PermissionError("La compra de entradas solo está permitida para usuarios registrados.")    
    
    def _validar_cantidad(self, cantidad: int):
        if cantidad <= 0 or cantidad > 10:
            # CA: La cantidad de entradas requeridas no debe ser mayor a 10.
            raise ValueError("La cantidad de entradas debe ser un número entre 1 y 10.")
    
    def _validar_fecha(self, fecha_visita: date):
        if fecha_visita in self.DIAS_PARQUE_CERRADO:
            # PU: Probar comprar entradas ingresando una fecha... parque cerrado (falla).
            raise ValueError(f"El parque se encuentra cerrado el día {fecha_visita}.")
        if fecha_visita < date.today():
            raise ValueError("La fecha de visita no puede ser en el pasado.")
    
    def _validar_forma_pago(self, forma_pago: str):
        if forma_pago is None or forma_pago.strip() == "":
            # PU: Probar comprar entradas sin seleccionar forma de pago (falla).
            raise ValueError("Debe seleccionar una forma de pago para completar la compra.")
    
    def validar_capacidad(self, fecha_visita: date, cantidad: int):
        # Consultar entradas ya vendidas para esa fecha
        entradas_vendidas = self.db.obtener_entradas_por_fecha(fecha_visita.strftime("%Y-%m-%d"))
        
        if cantidad > self.CAPACIDAD_MAXIMA:
            raise ValueError("No hay suficiente capacidad para la cantidad de entradas solicitadas.")
        
        if entradas_vendidas + cantidad > self.CAPACIDAD_MAXIMA:
            disponibles = self.CAPACIDAD_MAXIMA - entradas_vendidas
            raise ValueError(f"Solo quedan {disponibles} entradas disponibles para esa fecha.")

    def _validar_detalles_visitantes(self, cantidad: int, detalles_visitantes: list, tipo_pase: str):
        if len(detalles_visitantes) != cantidad:
            raise ValueError("El número de detalles de los visitantes no coincide con la cantidad de entradas.")
        for visitante in detalles_visitantes:
            if visitante.get("edad", -1) < 0:
                raise ValueError("La edad de los visitantes debe ser un número positivo.")
        if tipo_pase not in self.PASES_VALIDOS:
            raise ValueError(f"El tipo de pase '{tipo_pase}' no es válido. Opciones: {self.PASES_VALIDOS}")

    def _procesar_pago(self, forma_pago: str) -> bool:
        """Procesa el pago según la forma seleccionada"""
        if forma_pago == "tarjeta":
            # Simulación de redirección a Mercado Pago
            print("Redirigiendo a Mercado Pago para procesar pago con tarjeta...")
            return True
        elif forma_pago == "efectivo":
            print("Pago en efectivo será procesado en boletería.")
            return True
        return True
    
    def _enviar_mail_confirmacion(self, detalles_compra: dict):
        """Envía mail de confirmación de la compra"""
        print(f"Enviando mail de confirmación: {detalles_compra}")
        # Aquí iría la lógica real de envío de email
        return True
    
    # Métodos adicionales para gestión de usuarios
    def registrar_usuario(self, email: str, nombre: str) -> int:
        """Registra un nuevo usuario en el sistema"""
        return self.db.registrar_usuario(email, nombre)
    
    def obtener_compra(self, compra_id: int) -> dict:
        """Obtiene los detalles de una compra"""
        return self.db.obtener_compra(compra_id)
    
    def obtener_disponibilidad(self, fecha_visita: date) -> int:
        """Obtiene las entradas disponibles para una fecha"""
        entradas_vendidas = self.db.obtener_entradas_por_fecha(fecha_visita.strftime("%Y-%m-%d"))
        return self.CAPACIDAD_MAXIMA - entradas_vendidas