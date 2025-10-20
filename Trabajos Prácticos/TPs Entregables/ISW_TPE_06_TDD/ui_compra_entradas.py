"""
Interfaz gráfica PyQt5 para el sistema de compra de entradas del parque.
Implementa todos los criterios de aceptación de la historia de usuario.
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFormLayout, QGridLayout, QLabel, QPushButton, QLineEdit, 
    QSpinBox, QComboBox, QDateEdit, QGroupBox, QScrollArea,
    QMessageBox, QTextEdit, QCheckBox, QFrame, QProgressBar
)
from PyQt5.QtCore import QDate, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor
from datetime import date, timedelta
import traceback

# Agregar el directorio src al path para importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from src.gestor_entradas import GestorDeEntradas
    from src.database import DatabaseManager
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    print("Asegúrate de que los archivos database.py y gestor_entradas.py estén en el directorio src/")
    sys.exit(1)


class VisitanteWidget(QWidget):
    """Widget para capturar datos de un visitante individual"""
    
    def __init__(self, numero):
        super().__init__()
        self.numero = numero
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        
        # Etiqueta del visitante
        label = QLabel(f"Visitante {self.numero}:")
        label.setMinimumWidth(80)
        
        # Campo nombre
        self.nombre_edit = QLineEdit()
        self.nombre_edit.setPlaceholderText("Nombre completo")
        self.nombre_edit.setMinimumWidth(200)
        
        # Campo edad
        self.edad_spinbox = QSpinBox()
        self.edad_spinbox.setRange(0, 120)
        self.edad_spinbox.setValue(25)
        self.edad_spinbox.setSuffix(" años")
        
        layout.addWidget(label)
        layout.addWidget(QLabel("Nombre:"))
        layout.addWidget(self.nombre_edit)
        layout.addWidget(QLabel("Edad:"))
        layout.addWidget(self.edad_spinbox)
        
        self.setLayout(layout)
    
    def get_datos(self):
        """Retorna los datos del visitante"""
        return {
            "nombre": self.nombre_edit.text().strip(),
            "edad": self.edad_spinbox.value()
        }
    
    def es_valido(self):
        """Valida que los datos del visitante sean correctos"""
        edad = self.edad_spinbox.value()

        # La edad debe ser mayor o igual que 0
        if edad <= 0:
            return False

        return True


class PagoSimuladorDialog(QMessageBox):
    """Dialog que simula el proceso de pago"""
    
    def __init__(self, forma_pago, total, parent=None):
        super().__init__(parent)
        self.forma_pago = forma_pago
        self.total = total
        self.setup_ui()
    
    def setup_ui(self):
        if self.forma_pago == "tarjeta":
            self.setWindowTitle("Mercado Pago - Procesando Pago")
            self.setText(f"🔄 Redirigiendo a Mercado Pago...\n\nTotal a pagar: ${self.total:.2f}")
            self.setInformativeText("Simulando proceso de pago con tarjeta de crédito.\nEsto tomaría unos segundos en un entorno real.")
        else:
            self.setWindowTitle("Pago en Efectivo")
            self.setText(f"💰 Pago en Boletería\n\nTotal a pagar: ${self.total:.2f}")
            self.setInformativeText("Deberá abonar en efectivo al momento de retirar las entradas en boletería.")
        
        self.setIcon(QMessageBox.Information)
        self.addButton("Confirmar Pago", QMessageBox.AcceptRole)
        self.addButton("Cancelar", QMessageBox.RejectRole)


class CompraExitosaDialog(QMessageBox):
    """Dialog que muestra el resultado exitoso de la compra"""
    
    def __init__(self, resultado, parent=None):
        super().__init__(parent)
        self.resultado = resultado
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("¡Compra Realizada con Éxito!")
        self.setIcon(QMessageBox.Information)
        
        mensaje = f"""
            ✅ {self.resultado['mensaje']}

            📋 Detalles de la compra:
            • ID de Compra: {self.resultado['compra_id']}
            • Cantidad de entradas: {self.resultado['cantidad_entradas']}
            • Fecha de visita: {self.resultado['fecha_visita']}

            📧 Se ha enviado un email de confirmación con todos los detalles.

            ¡Gracias por elegirnos para su visita al parque!
                    """
        
        self.setText(mensaje)
        self.addButton("Cerrar", QMessageBox.AcceptRole)


class CompraEntradasWindow(QMainWindow):
    """Ventana principal para la compra de entradas"""
    
    def __init__(self):
        super().__init__()
        self.gestor = None
        self.visitantes_widgets = []
        self.init_gestor()
        self.init_ui()
        self.setup_conexiones()
        self.actualizar_disponibilidad()
    
    def init_gestor(self):
        """Inicializa el gestor de entradas"""
        try:
            self.gestor = GestorDeEntradas()
            # Registrar algunos usuarios de ejemplo si no existen
            try:
                self.gestor.registrar_usuario("juan.perez@email.com", "Juan Pérez")
                self.gestor.registrar_usuario("ana.garcia@email.com", "Ana García")
                self.gestor.registrar_usuario("luis.martinez@email.com", "Luis Martínez")
            except Exception:
                pass  # Usuarios ya existen
        except Exception as e:
            QMessageBox.critical(None, "Error", f"No se pudo inicializar el sistema:\n{e}")
            sys.exit(1)
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.setWindowTitle("Sistema de Compra de Entradas - Parque Temático")
        self.setMinimumSize(800, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Título
        titulo = QLabel("🎢 Compra de Entradas - Parque Temático")
        titulo.setFont(QFont("Arial", 18, QFont.Bold))
        titulo.setStyleSheet("color: #2E86AB; margin: 10px;")
        main_layout.addWidget(titulo)
        
        # Scroll area para el formulario
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Sección 1: Datos del usuario
        usuario_group = self.crear_seccion_usuario()
        scroll_layout.addWidget(usuario_group)
        
        # Sección 2: Datos de la visita
        visita_group = self.crear_seccion_visita()
        scroll_layout.addWidget(visita_group)

        # Sección 3: Pago
        pago_group = self.crear_seccion_pago()
        scroll_layout.addWidget(pago_group)
        
        # Botones principales
        botones_layout = QHBoxLayout()
        
        self.btn_comprar = QPushButton("💳 Comprar Entradas")
        self.btn_comprar.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_comprar.setStyleSheet("""
            QPushButton {
                background-color: #A23B72;
                color: white;
                padding: 12px;
                border-radius: 6px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #8B2F5F;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        
        self.btn_limpiar = QPushButton("🧹 Limpiar Formulario")
        self.btn_limpiar.setFont(QFont("Arial", 10))
        self.btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #F18F01;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D67E01;
            }
        """)
        
        botones_layout.addWidget(self.btn_limpiar)
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_comprar)
        
        main_layout.addLayout(botones_layout)

        # Sección 4: Visitantes
        self.visitantes_group = self.crear_seccion_visitantes()
        scroll_layout.addWidget(self.visitantes_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)
        
        # Barra de estado (información de disponibilidad)
        self.status_label = QLabel("Cargando información del parque...")
        self.status_label.setStyleSheet("padding: 5px; background-color: #F0F0F0;")
        main_layout.addWidget(self.status_label)
    
    def crear_seccion_usuario(self):
        """Crea la sección de datos del usuario"""
        group = QGroupBox("👤 Datos del Usuario Registrado")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        
        layout = QFormLayout()
        
        self.email_combo = QComboBox()
        self.email_combo.setEditable(True)
        self.email_combo.addItems([
            "juan.perez@email.com",
            "ana.garcia@email.com", 
            "luis.martinez@email.com"
        ])
        self.email_combo.setCurrentText("")
        self.email_combo.lineEdit().setPlaceholderText("Seleccione o ingrese su email")
        
        layout.addRow("📧 Email:", self.email_combo)
        
        # Nota informativa
        nota = QLabel("⚠️ Solo usuarios registrados pueden comprar entradas")
        nota.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
        layout.addRow("", nota)
        
        group.setLayout(layout)
        return group
    
    def crear_seccion_visita(self):
        """Crea la sección de datos de la visita"""
        group = QGroupBox("📅 Datos de la Visita")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        
        layout = QFormLayout()
        
        # Fecha de visita
        self.fecha_edit = QDateEdit()
        self.fecha_edit.setDate(QDate.currentDate().addDays(1))
        self.fecha_edit.setMinimumDate(QDate.currentDate())
        self.fecha_edit.setMaximumDate(QDate.currentDate().addYears(1))
        self.fecha_edit.setCalendarPopup(True)
        
        layout.addRow("📅 Fecha de visita:", self.fecha_edit)
        
        # Cantidad de entradas
        self.cantidad_spinbox = QSpinBox()
        self.cantidad_spinbox.setRange(1, 10)
        self.cantidad_spinbox.setValue(1)
        self.cantidad_spinbox.setSuffix(" entradas")
        
        layout.addRow("🎫 Cantidad:", self.cantidad_spinbox)
        
        # Tipo de pase
        self.tipo_pase_combo = QComboBox()
        self.tipo_pase_combo.addItems(["Regular", "VIP"])
        self.tipo_pase_combo.setStyleSheet("QComboBox { background-color: white; color: #212121; }")

        
        layout.addRow("⭐ Tipo de pase:", self.tipo_pase_combo)
        
        # Información de disponibilidad
        self.disponibilidad_label = QLabel("Verificando disponibilidad...")
        self.disponibilidad_label.setStyleSheet("color: #2E86AB; font-weight: bold;")
        layout.addRow("📊 Disponibilidad:", self.disponibilidad_label)
        
        group.setLayout(layout)
        return group
    
    def crear_seccion_visitantes(self):
        """Crea la sección de datos de visitantes"""
        group = QGroupBox("👥 Datos de los Visitantes")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        
        self.visitantes_layout = QVBoxLayout()
        
        # Crear el primer visitante
        self.actualizar_visitantes()
        
        group.setLayout(self.visitantes_layout)
        return group
    
    def crear_seccion_pago(self):
        """Crea la sección de forma de pago"""
        group = QGroupBox("💳 Forma de Pago")
        group.setFont(QFont("Arial", 11, QFont.Bold))
        
        layout = QFormLayout()
        
        self.forma_pago_combo = QComboBox()
        self.forma_pago_combo.addItem("Seleccione forma de pago", "")
        self.forma_pago_combo.addItem("💳 Tarjeta de Crédito (Mercado Pago)", "tarjeta")
        self.forma_pago_combo.addItem("💰 Efectivo en Boletería", "efectivo")
        self.forma_pago_combo.setStyleSheet("QComboBox { background-color: white; color: #212121; }")
        
        layout.addRow("💸 Forma de pago:", self.forma_pago_combo)
        
        # Información de pago
        info_pago = QLabel("💡 Tarjeta: Pago inmediato online | Efectivo: Pago al retirar entradas")
        info_pago.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
        layout.addRow("", info_pago)
        
        group.setLayout(layout)
        return group
    
    def setup_conexiones(self):
        """Configura las conexiones de señales"""
        self.cantidad_spinbox.valueChanged.connect(self.actualizar_visitantes)
        self.fecha_edit.dateChanged.connect(self.actualizar_disponibilidad)
        self.btn_comprar.clicked.connect(self.realizar_compra)
        self.btn_limpiar.clicked.connect(self.limpiar_formulario)
        self.email_combo.currentTextChanged.connect(self.validar_formulario)
        self.forma_pago_combo.currentTextChanged.connect(self.validar_formulario)
    
    def actualizar_visitantes(self):
        """Actualiza la lista de widgets de visitantes según la cantidad"""
        cantidad = self.cantidad_spinbox.value()
        
        # Limpiar widgets existentes
        for widget in self.visitantes_widgets:
            widget.setParent(None)
        self.visitantes_widgets.clear()
        
        # Crear nuevos widgets
        for i in range(cantidad):
            visitante_widget = VisitanteWidget(i + 1)
            self.visitantes_widgets.append(visitante_widget)
            self.visitantes_layout.addWidget(visitante_widget)
        
        # Espaciador
        self.visitantes_layout.addStretch()
        
        self.validar_formulario()
        self.actualizar_disponibilidad()
    
    def actualizar_disponibilidad(self):
        """Actualiza la información de disponibilidad para la fecha seleccionada"""
        try:
            fecha_seleccionada = self.fecha_edit.date().toPyDate()
            disponibles = self.gestor.obtener_disponibilidad(fecha_seleccionada)
            cantidad = self.cantidad_spinbox.value()
            
            if disponibles >= cantidad:
                color = "#27AE60"  # Verde
                mensaje = f"✅ {disponibles} entradas disponibles"
            elif disponibles > 0:
                color = "#F39C12"  # Naranja
                mensaje = f"⚠️ Solo {disponibles} entradas disponibles"
            else:
                color = "#E74C3C"  # Rojo
                mensaje = "❌ No hay entradas disponibles"
            
            self.disponibilidad_label.setText(mensaje)
            self.disponibilidad_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            # Actualizar status bar
            self.status_label.setText(f"Fecha: {fecha_seleccionada.strftime('%d/%m/%Y')} | {mensaje}")
            
        except Exception as e:
            self.disponibilidad_label.setText(f"Error: {e}")
            self.disponibilidad_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
    
    def validar_formulario(self):
        """Valida el formulario y habilita/deshabilita el botón de compra"""
        valido = True
        
        # Validar email
        if not self.email_combo.currentText().strip():
            valido = False
        
        # Validar forma de pago
        if not self.forma_pago_combo.currentData():
            valido = False
        
        # Validar visitantes (se validará en tiempo de compra)
        
        self.btn_comprar.setEnabled(valido)
    
    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.email_combo.setCurrentText("")
        self.fecha_edit.setDate(QDate.currentDate().addDays(1))
        self.cantidad_spinbox.setValue(1)
        self.tipo_pase_combo.setCurrentIndex(0)
        self.forma_pago_combo.setCurrentIndex(0)
        
        # Limpiar visitantes se hace automáticamente al cambiar cantidad
        self.actualizar_disponibilidad()
    
    def realizar_compra(self):
        """Procesa la compra de entradas"""
        print("Iniciando proceso de compra...")
        try:
            # Recopilar datos del formulario
            email = self.email_combo.currentText().strip()
            fecha_visita = self.fecha_edit.date().toPyDate()
            cantidad = self.cantidad_spinbox.value()
            tipo_pase = self.tipo_pase_combo.currentText()
            forma_pago = self.forma_pago_combo.currentData()
            # Validar visitantes
            visitantes_datos = []
            for widget in self.visitantes_widgets:
                if not widget.es_valido():
                    QMessageBox.warning(self, "Datos Incompletos", 
                                      f"Por favor complete los datos del {widget.numero}° visitante.")
                    return
                visitantes_datos.append(widget.get_datos())
            
            # Calcular total estimado
            precios = {"Regular": 25.00, "VIP": 45.00}
            total_estimado = cantidad * precios.get(tipo_pase, 25.00)
            
            # Mostrar confirmación
            confirmacion = QMessageBox.question(
                self, "Confirmar Compra",
                f"¿Confirma la compra de {cantidad} entrada(s) {tipo_pase}?\n\n"
                f"Fecha: {fecha_visita.strftime('%d/%m/%Y')}\n"
                f"Total estimado: ${total_estimado:.2f}\n"
                f"Forma de pago: {self.forma_pago_combo.currentText()}",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirmacion != QMessageBox.Yes:
                return
            # Simular proceso de pago
            pago_dialog = PagoSimuladorDialog(forma_pago, total_estimado, self)
            # Realizar la compra
            resultado = self.gestor.comprar_entradas(
                fecha_visita=fecha_visita,
                cantidad=cantidad,
                detalles_visitantes=visitantes_datos,
                tipo_pase=tipo_pase,
                forma_pago=forma_pago,
                usuario_email=email
            )
            
            # Mostrar resultado exitoso
            print(resultado)
            CompraExitosaDialog(resultado, self).exec_()
            
            # Limpiar formulario y actualizar disponibilidad
            self.limpiar_formulario()
            
        except PermissionError as e:
            QMessageBox.warning(self, "Usuario No Registrado", str(e))
        except ValueError as e:
            QMessageBox.warning(self, "Error en los Datos", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error Inesperado", 
                               f"Ocurrió un error al procesar la compra:\n{str(e)}\n\n"
                               f"Detalles técnicos:\n{traceback.format_exc()}")


def main():
    """Función principal para ejecutar la aplicación"""
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')
    
    # Paleta de colores moderna
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(248, 248, 248))
    palette.setColor(QPalette.WindowText, QColor(33, 33, 33))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))  # Fondo blanco para campos editables
    palette.setColor(QPalette.Text, QColor(33, 33, 33))     # Texto oscuro
    app.setPalette(palette)
    
    # Crear y mostrar la ventana principal
    window = CompraEntradasWindow()
    window.show()
    
    # Ejecutar la aplicación
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
