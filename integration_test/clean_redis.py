#!/usr/bin/env python3
"""
Script para limpiar el entorno de Redis para la prueba de Independiente vs Huracán.
Eliminará el grupo de consumidores y el stream si existe.
"""

import redis
import os
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
STREAM_NAME = os.getenv('REDIS_STREAM_NAME', 'comment_stream:independiente_huracan_test')
GROUP_NAME = os.getenv('REDIS_CONSUMER_GROUP_NAME', 'test_processing_group')

print(f"\n{'='*70}")
print(f"LIMPIEZA DE REDIS PARA PRUEBAS DE INTEGRACIÓN")
print(f"{'='*70}")
print(f"Host: {REDIS_HOST}:{REDIS_PORT}")
print(f"Stream: {STREAM_NAME}")
print(f"Grupo: {GROUP_NAME}")
print(f"{'='*70}\n")

# Conectar a Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    # Verificar conexión
    r.ping()
    print("✅ Conexión a Redis establecida correctamente.")
except Exception as e:
    print(f"❌ Error al conectar a Redis: {e}")
    exit(1)

def clean_stream():
    """Limpia el stream y el grupo de consumidores"""
    # Verificar si el stream existe
    if r.exists(STREAM_NAME):
        print(f"ℹ️ Stream '{STREAM_NAME}' existe.")
        
        # Información de las entradas
        stream_length = r.xlen(STREAM_NAME)
        print(f"ℹ️ El stream tiene {stream_length} mensajes.")
        
        # Verificar si el grupo existe
        try:
            groups = r.xinfo_groups(STREAM_NAME)
            for group in groups:
                if group['name'] == GROUP_NAME:
                    print(f"ℹ️ Grupo '{GROUP_NAME}' encontrado.")
                    
                    # Información de los consumidores
                    consumers = r.xinfo_consumers(STREAM_NAME, GROUP_NAME)
                    print(f"ℹ️ El grupo tiene {len(consumers)} consumidores:")
                    for consumer in consumers:
                        print(f"  - {consumer['name']}: {consumer['pending']} mensajes pendientes, inactivo por {consumer['inactive']/1000:.1f} segundos")
                    
                    # Eliminar el grupo
                    try:
                        r.xgroup_destroy(STREAM_NAME, GROUP_NAME)
                        print(f"✅ Grupo '{GROUP_NAME}' eliminado.")
                    except Exception as e:
                        print(f"❌ Error al eliminar grupo '{GROUP_NAME}': {e}")
                    break
            else:
                print(f"ℹ️ No se encontró el grupo '{GROUP_NAME}'.")
        except Exception as e:
            print(f"❌ Error al obtener información del grupo: {e}")
        
        # Eliminar el stream
        try:
            r.delete(STREAM_NAME)
            print(f"✅ Stream '{STREAM_NAME}' eliminado.")
        except Exception as e:
            print(f"❌ Error al eliminar stream '{STREAM_NAME}': {e}")
    else:
        print(f"ℹ️ Stream '{STREAM_NAME}' no existe.")

def verify_clean_state():
    """Verifica que el entorno está limpio"""
    print(f"\n{'='*70}")
    print("VERIFICACIÓN DEL ESTADO LIMPIO")
    print(f"{'='*70}")
    
    # Verificar que el stream no existe
    if not r.exists(STREAM_NAME):
        print(f"✅ Stream '{STREAM_NAME}' no existe.")
    else:
        print(f"❌ Stream '{STREAM_NAME}' todavía existe.")
        
    # Intentar obtener información del grupo (debería fallar)
    try:
        r.xinfo_groups(STREAM_NAME)
        print(f"❌ Todavía es posible obtener información de grupos para '{STREAM_NAME}'.")
    except redis.exceptions.ResponseError as e:
        if "no such key" in str(e).lower():
            print(f"✅ No hay grupos asociados con '{STREAM_NAME}'.")
        else:
            print(f"❌ Error inesperado al verificar grupos: {e}")
            
    print(f"{'='*70}\n")

# Ejecutar limpieza
clean_stream()

# Verificar estado limpio
verify_clean_state()

# Crear stream vacío (opcional)
create_empty_stream = False
if create_empty_stream:
    print("Creando stream vacío para pruebas...")
    r.xadd(STREAM_NAME, {"init": "true"}, id="0-0")
    print(f"✅ Stream '{STREAM_NAME}' creado (vacío).")

print("\nLimpieza completada. El entorno Redis está listo para pruebas.\n") 