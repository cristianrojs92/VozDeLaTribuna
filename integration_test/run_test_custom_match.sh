#!/bin/bash
# Script para ejecutar la prueba del procesador de comentarios con cualquier partido

# Verificar si se han proporcionado los argumentos necesarios
if [ "$#" -ne 2 ]; then
    echo "Error: Se requieren 2 argumentos - nombre del equipo local y nombre del equipo visitante"
    echo "Uso: ./run_test_custom_match.sh \"Nombre Equipo Local\" \"Nombre Equipo Visitante\""
    echo "Ejemplo: ./run_test_custom_match.sh \"River Plate\" \"Boca Juniors\""
    exit 1
fi

HOME_TEAM="$1"
AWAY_TEAM="$2"

# Crear IDs para el stream (convertir a minúsculas y reemplazar espacios)
HOME_ID=$(echo "$HOME_TEAM" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
AWAY_ID=$(echo "$AWAY_TEAM" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
STREAM_ID="comment_stream:${HOME_ID}_${AWAY_ID}_test"

echo "=== CONFIGURANDO ENTORNO PARA PRUEBA DE PARTIDO ==="
echo "$HOME_TEAM vs $AWAY_TEAM"

# Variables de entorno para el procesador
export MATCH_HOME_TEAM="$HOME_TEAM"
export MATCH_AWAY_TEAM="$AWAY_TEAM"
export MATCH_CONTEXT_ENABLED="true"
export REDIS_STREAM_NAME="$STREAM_ID" 
export REDIS_CONSUMER_GROUP_NAME="test_processing_group_${HOME_ID}_${AWAY_ID}"

echo ""
echo "Variables de entorno configuradas:"
echo "MATCH_HOME_TEAM=${MATCH_HOME_TEAM}"
echo "MATCH_AWAY_TEAM=${MATCH_AWAY_TEAM}"
echo "MATCH_CONTEXT_ENABLED=${MATCH_CONTEXT_ENABLED}"
echo "REDIS_STREAM_NAME=${REDIS_STREAM_NAME}"
echo "REDIS_CONSUMER_GROUP_NAME=${REDIS_CONSUMER_GROUP_NAME}"

# Crear un script de prueba personalizado
TEST_SCRIPT="integration_test/test_${HOME_ID}_${AWAY_ID}.py"
cat > "$TEST_SCRIPT" <<EOF
#!/usr/bin/env python3
"""
Script de prueba para un partido específico entre ${HOME_TEAM} vs ${AWAY_TEAM}.
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
REDIS_STREAM_NAME = os.getenv('REDIS_STREAM_NAME', '${STREAM_ID}')

# Específico del partido
HOME_TEAM = "${HOME_TEAM}"
AWAY_TEAM = "${AWAY_TEAM}"
EVENT_UUID = str(uuid.uuid4())  # ID único para este evento/partido

# Conectar a Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Comentarios de prueba específicos para este partido
# Puedes personalizar estos ejemplos según los equipos
test_comments = [
    # Menciones a equipos (usando diferentes alias)
    f"${HOME_TEAM} está jugando increíble este torneo, son una máquina",
    f"${AWAY_TEAM} no puede salir de su área",
    f"Qué partidazo entre ${HOME_TEAM} y ${AWAY_TEAM}",
    
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
        "stream_id": f"{HOME_TEAM.lower().replace(' ', '_')}_{AWAY_TEAM.lower().replace(' ', '_')}_test",
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

print("\\n=============================================================")
print(f"✅ Prueba completa. Se enviaron {len(test_comments)} comentarios para el partido {HOME_TEAM} vs {AWAY_TEAM}.")
print("=============================================================")
EOF

chmod +x "$TEST_SCRIPT"

echo ""
echo "=== INSTRUCCIONES ==="
echo "1. Script de prueba creado: $TEST_SCRIPT"
echo ""
echo "2. Abre una nueva terminal y ejecuta el procesador con estas variables:"
echo "   cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "   source integration_test/run_test_custom_match.sh \"$HOME_TEAM\" \"$AWAY_TEAM\""
echo "   python processors/comment_processor/comment_processor.py"
echo ""
echo "3. En otra terminal, ejecuta el script de prueba:"
echo "   cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "   export REDIS_STREAM_NAME=${REDIS_STREAM_NAME}"
echo "   python $TEST_SCRIPT"
echo ""
echo "Las variables de entorno están configuradas en esta terminal."
echo "Si ejecutas el procesador desde aquí, asegúrate de usar una nueva terminal para el script de prueba."