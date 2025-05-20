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
from datetime import datetime, timezone
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_STREAM_NAME = os.getenv('REDIS_STREAM_NAME', 'comment_stream:test')

# Específico del partido
HOME_TEAM = "Independiente"
AWAY_TEAM = "Huracán"
EVENT_UUID = str(uuid.uuid4())  # ID único para este evento/partido

# Conectar a Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

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
print(f"Event UUID: {EVENT_UUID}")
print("=============================================================")
print("Enviando comentarios de prueba. Asegúrate de tener el procesador")
print("ejecutándose con las variables de entorno correctas:")
print(f"  MATCH_HOME_TEAM={HOME_TEAM}")
print(f"  MATCH_AWAY_TEAM={AWAY_TEAM}")
print(f"  REDIS_STREAM_NAME={REDIS_STREAM_NAME}")
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