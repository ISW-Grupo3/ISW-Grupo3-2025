from datetime import date

# clase q gestiona la compra de entradas
class GestorDeEntradas:

    DIAS_PARQUE_CERRADO = [date(2025, 12, 25), date(2026, 1, 1)] 
    PASES_VALIDOS = ["Regular", "VIP", "Estudiante"]
    CAPACIDAD_MAXIMA = 100

    def comprar_entradas(self, fecha_visita: date, cantidad: int, detalles_visitantes: list, tipo_pase: str, forma_pago: str, usuario_registrado: bool) -> dict:
        self._validar_usuario(usuario_registrado)
        self._validar_cantidad(cantidad)
        self._validar_fecha(fecha_visita)
        self._validar_forma_pago(forma_pago)
        self.validar_capacidad(fecha_visita, cantidad)
        self._validar_detalles_visitantes(cantidad, detalles_visitantes, tipo_pase)

        self._procesar_pago(forma_pago)

        self.__enviar_mail_confirmacion({"cantidad": cantidad, "fecha": fecha_visita})
        return {
            "mensaje": "Compra realizada con éxito",
            "cantidad_entradas": cantidad,
            "fecha_visita": fecha_visita.strftime("%Y-%m-%d")
        }

    def _validar_usuario(self, usuario_registrado: bool):
        # CA: se debe permitir la compra de entradas solo a usuarios registrados.
        if not usuario_registrado:
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
        # Simulación: Asumimos que siempre hay capacidad (en un caso real, consultar
        # una base de datos o sistema de reservas)
        if cantidad > self.CAPACIDAD_MAXIMA:
            raise ValueError("No hay suficiente capacidad para la cantidad de entradas solicitadas.")

    def _validar_detalles_visitantes(self, cantidad: int, detalles_visitantes: list, tipo_pase: str):
        if len(detalles_visitantes) != cantidad:
            raise ValueError("El número de detalles de los visitantes no coincide con la cantidad de entradas.")
        for visitante in detalles_visitantes:
            if visitante.get("edad", -1) >0:
                raise ValueError("La edad de los visitantes debe ser un número positivo.")
        if tipo_pase not in self.PASES_VALIDOS:
            raise ValueError(f"El tipo de pase '{tipo_pase}' no es válido. Opciones: {self.PASES_VALIDOS}")

    def _procesar_pago(self, forma_pago: str) -> bool:
        if forma_pago == "tarjeta":
            return True
        return True
    
    def __enviar_mail_confirmacion(self, detalles_compra: dict):
        print(f"Enviando mail de confirmación: {detalles_compra}")
        return True