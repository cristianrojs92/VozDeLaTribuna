#!/bin/bash
# Script para ejecutar la prueba del procesador de comentarios en contexto de partido
# Independiente vs Huracán

echo "=== CONFIGURANDO ENTORNO PARA PRUEBA DE PARTIDO ==="
echo "Independiente vs Huracán"

# Variables de entorno para el procesador
export MATCH_HOME_TEAM="Independiente"
export MATCH_AWAY_TEAM="Huracán"
export MATCH_CONTEXT_ENABLED="true"
export REDIS_STREAM_NAME="comment_stream:independiente_huracan_test" 
export REDIS_CONSUMER_GROUP_NAME="test_processing_group"

echo ""
echo "Variables de entorno configuradas:"
echo "MATCH_HOME_TEAM=${MATCH_HOME_TEAM}"
echo "MATCH_AWAY_TEAM=${MATCH_AWAY_TEAM}"
echo "MATCH_CONTEXT_ENABLED=${MATCH_CONTEXT_ENABLED}"
echo "REDIS_STREAM_NAME=${REDIS_STREAM_NAME}"
echo "REDIS_CONSUMER_GROUP_NAME=${REDIS_CONSUMER_GROUP_NAME}"

echo ""
echo "=== INSTRUCCIONES ==="
echo "1. Abre una nueva terminal y ejecuta el procesador con estas variables:"
echo "   cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "   source run_test_independiente_huracan.sh"
echo "   python processors/comment_processor/comment_processor.py"
echo ""
echo "2. En otra terminal, ejecuta el script de prueba:"
echo "   cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "   export REDIS_STREAM_NAME=${REDIS_STREAM_NAME}"
echo "   python test_independiente_huracan.py"
echo ""
echo "Las variables de entorno están configuradas en esta terminal."
echo "Si ejecutas el procesador desde aquí, asegúrate de usar una nueva terminal para el script de prueba."