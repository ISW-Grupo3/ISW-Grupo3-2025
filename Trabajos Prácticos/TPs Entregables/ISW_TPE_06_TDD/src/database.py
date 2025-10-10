import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    """Gestor de base de datos SQLite para el sistema de entradas"""
    
    def __init__(self, db_path: str = "parque_entradas.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas necesarias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de usuarios registrados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activo BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabla de compras de entradas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    fecha_visita DATE NOT NULL,
                    cantidad_entradas INTEGER NOT NULL,
                    tipo_pase TEXT NOT NULL,
                    forma_pago TEXT NOT NULL,
                    estado_pago TEXT DEFAULT 'pendiente',
                    total DECIMAL(10,2),
                    fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmacion_enviada BOOLEAN DEFAULT 0,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            ''')
            
            # Tabla de visitantes por compra
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visitantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compra_id INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    edad INTEGER NOT NULL,
                    FOREIGN KEY (compra_id) REFERENCES compras (id)
                )
            ''')
            
            # Tabla de configuración del parque
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracion_parque (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capacidad_maxima INTEGER DEFAULT 100,
                    precio_regular DECIMAL(5,2) DEFAULT 25.00,
                    precio_vip DECIMAL(5,2) DEFAULT 45.00,
                    precio_estudiante DECIMAL(5,2) DEFAULT 15.00
                )
            ''')
            
            # Tabla de días cerrados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dias_cerrados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE UNIQUE NOT NULL,
                    motivo TEXT
                )
            ''')
            
            conn.commit()
            self._insert_initial_data()
    
    def _insert_initial_data(self):
        """Inserta datos iniciales si no existen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insertar configuración inicial si no existe
            cursor.execute("SELECT COUNT(*) FROM configuracion_parque")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO configuracion_parque (capacidad_maxima, precio_regular, precio_vip, precio_estudiante)
                    VALUES (100, 25.00, 45.00, 15.00)
                ''')
            
            # Insertar días cerrados por defecto
            dias_cerrados = [
                ('2025-12-25', 'Navidad'),
                ('2026-01-01', 'Año Nuevo')
            ]
            
            for fecha, motivo in dias_cerrados:
                cursor.execute('''
                    INSERT OR IGNORE INTO dias_cerrados (fecha, motivo)
                    VALUES (?, ?)
                ''', (fecha, motivo))
            
            conn.commit()
    
    def usuario_registrado(self, email: str) -> bool:
        """Verifica si un usuario está registrado por email"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM usuarios 
                WHERE email = ? AND activo = 1
            ''', (email,))
            return cursor.fetchone()[0] > 0
    
    def registrar_usuario(self, email: str, nombre: str) -> int:
        """Registra un nuevo usuario y retorna su ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO usuarios (email, nombre)
                VALUES (?, ?)
            ''', (email, nombre))
            conn.commit()
            return cursor.lastrowid
    
    def obtener_usuario_por_email(self, email: str) -> Optional[Dict]:
        """Obtiene los datos de un usuario por email"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM usuarios 
                WHERE email = ? AND activo = 1
            ''', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def obtener_dias_cerrados(self) -> List[str]:
        """Obtiene la lista de días en que el parque está cerrado"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT fecha FROM dias_cerrados')
            return [row[0] for row in cursor.fetchall()]
    
    def obtener_configuracion_parque(self) -> Dict:
        """Obtiene la configuración actual del parque"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM configuracion_parque LIMIT 1')
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    def crear_compra(self, usuario_email: str, fecha_visita: str, cantidad: int, 
                    visitantes: List[Dict], tipo_pase: str, forma_pago: str) -> int:
        """Crea una nueva compra de entradas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Obtener usuario
            usuario = self.obtener_usuario_por_email(usuario_email)
            if not usuario:
                raise ValueError("Usuario no encontrado")
            
            # Calcular total
            config = self.obtener_configuracion_parque()
            precio_por_entrada = {
                'Regular': config.get('precio_regular', 25.00),
                'VIP': config.get('precio_vip', 45.00),
                'Estudiante': config.get('precio_estudiante', 15.00)
            }
            total = cantidad * precio_por_entrada.get(tipo_pase, 25.00)
            
            # Crear compra
            cursor.execute('''
                INSERT INTO compras (usuario_id, fecha_visita, cantidad_entradas, 
                                   tipo_pase, forma_pago, total)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (usuario['id'], fecha_visita, cantidad, tipo_pase, forma_pago, total))
            
            compra_id = cursor.lastrowid
            
            # Insertar visitantes
            for visitante in visitantes:
                cursor.execute('''
                    INSERT INTO visitantes (compra_id, nombre, edad)
                    VALUES (?, ?, ?)
                ''', (compra_id, visitante['nombre'], visitante['edad']))
            
            conn.commit()
            return compra_id
    
    def obtener_compra(self, compra_id: int) -> Optional[Dict]:
        """Obtiene los detalles de una compra por ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Obtener datos de la compra
            cursor.execute('''
                SELECT c.*, u.email, u.nombre as nombre_usuario
                FROM compras c
                JOIN usuarios u ON c.usuario_id = u.id
                WHERE c.id = ?
            ''', (compra_id,))
            
            compra = cursor.fetchone()
            if not compra:
                return None
            
            compra_dict = dict(compra)
            
            # Obtener visitantes
            cursor.execute('''
                SELECT nombre, edad FROM visitantes
                WHERE compra_id = ?
            ''', (compra_id,))
            
            compra_dict['visitantes'] = [dict(row) for row in cursor.fetchall()]
            return compra_dict
    
    def marcar_confirmacion_enviada(self, compra_id: int):
        """Marca una compra como confirmación enviada"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE compras 
                SET confirmacion_enviada = 1 
                WHERE id = ?
            ''', (compra_id,))
            conn.commit()
    
    def actualizar_estado_pago(self, compra_id: int, estado: str):
        """Actualiza el estado de pago de una compra"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE compras 
                SET estado_pago = ? 
                WHERE id = ?
            ''', (estado, compra_id))
            conn.commit()
    
    def obtener_entradas_por_fecha(self, fecha: str) -> int:
        """Obtiene la cantidad de entradas vendidas para una fecha específica"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(SUM(cantidad_entradas), 0)
                FROM compras 
                WHERE fecha_visita = ? AND estado_pago != 'cancelado'
            ''', (fecha,))
            return cursor.fetchone()[0]
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        pass  # SQLite se cierra automáticamente con context manager
