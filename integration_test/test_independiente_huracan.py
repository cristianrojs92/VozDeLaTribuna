#!/usr/bin/env python3
"""
Script de prueba para un partido específico entre Independiente vs Huracán.
Este script envía comentarios de prueba al stream de Redis con el contexto del partido.
"""

import redis
import json
import time
import uuid
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_STREAM_NAME = os.getenv('REDIS_STREAM_NAME', 'comment_stream:test')
REDIS_CONSUMER_GROUP_NAME = os.getenv('REDIS_CONSUMER_GROUP_NAME', 'test_processing_group')

# Específico del partido
HOME_TEAM = "Independiente"
AWAY_TEAM = "Huracán"
EVENT_UUID = str(uuid.uuid4())  # ID único para este evento/partido

# Conectar a Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Función para verificar si el grupo de consumidores existe
def check_consumer_group_exists(redis_client, stream_name, group_name):
    try:
        # Intentamos obtener información sobre el grupo
        info = redis_client.xinfo_groups(stream_name)
        for group in info:
            # Acceder al nombre del grupo de manera segura, considerando diferentes versiones de Redis
            group_name_bytes = group.get(b'name')
            if group_name_bytes is None:
                group_name_bytes = group.get('name')  # Algunas versiones usan str como clave
            
            # Convertir a string si es necesario
            if group_name_bytes is not None:
                if isinstance(group_name_bytes, bytes):
                    actual_name = group_name_bytes.decode('utf-8')
                else:
                    actual_name = str(group_name_bytes)
                
                if actual_name == group_name:
                    return True
        return False
    except redis.exceptions.ResponseError as e:
        # Si el stream no existe, devolvemos False
        if "no such key" in str(e).lower():
            return False
        else:
            raise

# Esperar a que el grupo de consumidores exista
max_retries = 10
retry_count = 0
print(f"Verificando si el grupo de consumidores '{REDIS_CONSUMER_GROUP_NAME}' existe en stream '{REDIS_STREAM_NAME}'...")

while retry_count < max_retries:
    if check_consumer_group_exists(r, REDIS_STREAM_NAME, REDIS_CONSUMER_GROUP_NAME):
        print(f"✅ Grupo '{REDIS_CONSUMER_GROUP_NAME}' encontrado. Procediendo a enviar mensajes.")
        break
    else:
        retry_count += 1
        print(f"⏳ Esperando a que el procesador cree el grupo de consumidores... ({retry_count}/{max_retries})")
        time.sleep(2)  # Esperar 2 segundos antes de verificar nuevamente

if retry_count >= max_retries:
    print(f"❌ El grupo de consumidores '{REDIS_CONSUMER_GROUP_NAME}' no existe después de {max_retries} intentos.")
    print("   Asegúrate de que el procesador esté en ejecución y configurado correctamente.")
    print("   Deteniendo el script...")
    sys.exit(1)

# Comentarios de prueba específicos para Independiente vs Huracán
test_comments = [
    # Menciones a equipos (usando diferentes alias)
    "El Rojo está jugando increíble este torneo, son una máquina",
    "Los Diablos Rojos dominan la posesión",
    "Independiente presiona mucho",
    "El Globo está muy defensivo hoy",
    "Huracán no puede salir de su área",
    "El Quemero hoy no encuentra la pelota",
    
    # Menciones a jugadores de Independiente (con sentimiento)
    "Rey de Independiente está atento en el arco",
    "Gran partido de Rodrigo Rey, salvó al Rojo",
    "Laso es un desastre en la defensa del Rojo",
    "Saltita González se está comiendo la cancha",
    
    # Menciones a jugadores de Huracán (con sentimiento)
    "Walter Mazzantti es un crack, el único que intenta algo en el Globo",
    "Cabral no puede dar un pase bien, horrible",
    "Gran atajada de Chaves para el Globo",
    
    # Comentarios complejos con múltiples entidades
    "Mazzantti del Globo está imparable pero Rey del Rojo le ataja todo",
    "El partido está aburrido, ni Independiente ni Huracán generan peligro",
    
    # Ambigüedad que debería resolverse con el contexto (Marcos Rojo de Boca vs el Rojo)
    "El rojo tiene que mejorar mucho en defensa",
    "A Rojo le falta intensidad en el mediocampo",
    
    # Comentarios neutrales o ambiguos
    "El árbitro está dejando jugar",
    "Qué partido aburrido, ninguno propone nada",
    "El VAR debería revisar esa jugada"
]

print("=============================================================")
print(f"PRUEBA DEL MVP: PARTIDO {HOME_TEAM} vs {AWAY_TEAM}")
print(f"Stream de Redis: {REDIS_STREAM_NAME}")
print(f"Grupo de consumidores: {REDIS_CONSUMER_GROUP_NAME}")
print(f"Event UUID: {EVENT_UUID}")
print("=============================================================")
print("Enviando comentarios de prueba. Asegúrate de tener el procesador")
print("ejecutándose con las variables de entorno correctas:")
print(f"  MATCH_HOME_TEAM={HOME_TEAM}")
print(f"  MATCH_AWAY_TEAM={AWAY_TEAM}")
print(f"  REDIS_STREAM_NAME={REDIS_STREAM_NAME}")
print(f"  REDIS_CONSUMER_GROUP_NAME={REDIS_CONSUMER_GROUP_NAME}")
print("=============================================================")

# Enviar comentarios al stream de Redis
for i, comment_text in enumerate(test_comments):
    comment = {
        "event_uuid": EVENT_UUID,
        "stream_id": f"{HOME_TEAM.lower()}_{AWAY_TEAM.lower()}_test",
        "platform_source": "test",
        "capture_timestamp_utc": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        "author_display_name": f"TestUser{i}",
        "original_text": comment_text,
        "source_comment_id": f"test_comment_{i}",
        "platform_author_id": f"user_{i}"
    }
    
    # Enviar a Redis stream
    r.xadd(REDIS_STREAM_NAME, {"payload": json.dumps(comment)})
    print(f"Enviado [{i+1}/{len(test_comments)}]: {comment_text}")
    time.sleep(0.5)  # Pausa para simular comentarios en tiempo real

print("\n=============================================================")
print(f"✅ Prueba completa. Se enviaron {len(test_comments)} comentarios para el partido {HOME_TEAM} vs {AWAY_TEAM}.")
print("=============================================================")