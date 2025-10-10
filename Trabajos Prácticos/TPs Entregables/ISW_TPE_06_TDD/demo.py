#!/usr/bin/env python3
"""
Script de ejemplo para demostrar el uso del sistema de compra de entradas
con persistencia SQLite.
"""

from datetime import date, timedelta
from src.gestor_entradas import GestorDeEntradas
from src.database import DatabaseManager

def main():
    print("=== SISTEMA DE COMPRA DE ENTRADAS - PARQUE ===\n")
    
    # Inicializar el sistema
    gestor = GestorDeEntradas("parque_entradas_demo.db")
    
    # Registrar algunos usuarios de ejemplo
    print("1. Registrando usuarios de ejemplo...")
    try:
        usuario1_id = gestor.registrar_usuario("ana.garcia@email.com", "Ana García")
        usuario2_id = gestor.registrar_usuario("luis.perez@email.com", "Luis Pérez")
        print(f"✓ Usuario Ana registrado con ID: {usuario1_id}")
        print(f"✓ Usuario Luis registrado con ID: {usuario2_id}")
    except Exception as e:
        print(f"Usuarios ya existían: {e}")
    
    print("\n2. Consultando disponibilidad...")
    fecha_visita = date.today() + timedelta(days=15)
    disponibles = gestor.obtener_disponibilidad(fecha_visita)
    print(f"✓ Entradas disponibles para {fecha_visita}: {disponibles}")
    
    print("\n3. Realizando compra exitosa...")
    try:
        resultado = gestor.comprar_entradas(
            fecha_visita=fecha_visita,
            cantidad=3,
            detalles_visitantes=[
                {"nombre": "Ana García", "edad": 28},
                {"nombre": "Pedro García", "edad": 35},
                {"nombre": "Sofía García", "edad": 8}
            ],
            tipo_pase="VIP",
            forma_pago="tarjeta",
            usuario_email="ana.garcia@email.com"
        )
        
        print(f"✓ Compra exitosa:")
        print(f"  - ID de compra: {resultado['compra_id']}")
        print(f"  - Cantidad: {resultado['cantidad_entradas']} entradas")
        print(f"  - Fecha de visita: {resultado['fecha_visita']}")
        
        # Consultar detalles de la compra
        compra = gestor.obtener_compra(resultado['compra_id'])
        print(f"  - Total pagado: ${compra['total']}")
        print(f"  - Visitantes: {len(compra['visitantes'])}")
        
    except Exception as e:
        print(f"✗ Error en la compra: {e}")
    
    print("\n4. Consultando disponibilidad actualizada...")
    disponibles = gestor.obtener_disponibilidad(fecha_visita)
    print(f"✓ Entradas disponibles ahora: {disponibles}")
    
    print("\n5. Probando casos de fallo...")
    
    # Usuario no registrado
    try:
        gestor.comprar_entradas(
            fecha_visita, 1, [{"nombre": "Juan", "edad": 30}],
            "Regular", "efectivo", "noexiste@email.com"
        )
    except PermissionError as e:
        print(f"✓ Error esperado - Usuario no registrado: {e}")
    
    # Fecha en el pasado
    try:
        gestor.comprar_entradas(
            date.today() - timedelta(days=1), 1, [{"nombre": "Juan", "edad": 30}],
            "Regular", "efectivo", "ana.garcia@email.com"
        )
    except ValueError as e:
        print(f"✓ Error esperado - Fecha pasada: {e}")
    
    # Cantidad excesiva
    try:
        gestor.comprar_entradas(
            fecha_visita, 15, [{"nombre": f"Visitante{i}", "edad": 25} for i in range(15)],
            "Regular", "efectivo", "ana.garcia@email.com"
        )
    except ValueError as e:
        print(f"✓ Error esperado - Cantidad excesiva: {e}")
    
    # Día cerrado
    try:
        gestor.comprar_entradas(
            date(2025, 12, 25), 1, [{"nombre": "Juan", "edad": 30}],
            "Regular", "efectivo", "ana.garcia@email.com"
        )
    except ValueError as e:
        print(f"✓ Error esperado - Parque cerrado: {e}")
    
    print("\n=== DEMOSTRACIÓN COMPLETADA ===")
    print(f"\nBase de datos creada en: parque_entradas_demo.db")
    print("Puedes inspeccionar la base de datos con cualquier visor SQLite.")

if __name__ == "__main__":
    main()
