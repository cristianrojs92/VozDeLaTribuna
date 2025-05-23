#!/bin/bash
# run_test_independiente_huracan_completo.sh
# Script mejorado para configurar y ejecutar la prueba completa del sistema
# para el partido Independiente vs Huracán con los tres componentes

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== CONFIGURANDO ENTORNO PARA PRUEBA COMPLETA DEL SISTEMA ===${NC}"
echo -e "${BLUE}Independiente vs Huracán${NC}"
echo -e "${BLUE}(YouTube Producer + Comment Processor + Database Writer)${NC}"
echo ""

# Generar un UUID para el evento
EVENT_UUID=$(python -c "import uuid; print(uuid.uuid4())")

# Variables comunes
export REDIS_HOST="localhost"
export REDIS_PORT=6379
export EVENT_UUID="$EVENT_UUID"

# ----- CONFIGURACIÓN YOUTUBE PRODUCER -----
export YOUTUBE_VIDEO_ID="l5JICYBZUQw"  # ID de video de ejemplo - reemplazar con un ID real

# ----- CONFIGURACIÓN COMMENT PROCESSOR -----
export MATCH_HOME_TEAM="Independiente"
export MATCH_AWAY_TEAM="Huracán"
export MATCH_CONTEXT_ENABLED="true"
export REDIS_STREAM_NAME="comment_stream:independiente_huracan_test"
export REDIS_CONSUMER_GROUP_NAME="test_processing_group"
export REDIS_CONSUMER_NAME="processor_instance_test"
export REDIS_PROCESSED_STREAM="comment_stream:processed"

# ----- CONFIGURACIÓN DATABASE WRITER -----
export REDIS_CONSUMER_GROUP="database_writer_group"
export REDIS_CONSUMER_NAME="db_writer_test_instance"
export SUPABASE_URL="https://cxnqyytqsnjcmpbijczp.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4bnF5eXRxc25qY21wYmlqY3pwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5ODY1MjYsImV4cCI6MjA2MzU2MjUyNn0.0AmNIoJ8rSpvtxGWgkWaJPGl14vxhkqndNWjcD_UmkA"

echo -e "${YELLOW}Variables de entorno configuradas:${NC}"
echo -e "${GREEN}Configuración Común:${NC}"
echo "REDIS_HOST=${REDIS_HOST}"
echo "REDIS_PORT=${REDIS_PORT}"
echo "EVENT_UUID=${EVENT_UUID}"
echo ""
echo -e "${GREEN}YouTube Producer:${NC}"
echo "YOUTUBE_VIDEO_ID=${YOUTUBE_VIDEO_ID}"
echo ""
echo -e "${GREEN}Comment Processor:${NC}"
echo "MATCH_HOME_TEAM=${MATCH_HOME_TEAM}"
echo "MATCH_AWAY_TEAM=${MATCH_AWAY_TEAM}"
echo "MATCH_CONTEXT_ENABLED=${MATCH_CONTEXT_ENABLED}"
echo "REDIS_STREAM_NAME=${REDIS_STREAM_NAME}"
echo "REDIS_CONSUMER_GROUP_NAME=${REDIS_CONSUMER_GROUP_NAME}"
echo "REDIS_CONSUMER_NAME=${REDIS_CONSUMER_NAME}"
echo "REDIS_PROCESSED_STREAM=${REDIS_PROCESSED_STREAM}"
echo ""
echo -e "${GREEN}Database Writer:${NC}"
echo "REDIS_CONSUMER_GROUP=${REDIS_CONSUMER_GROUP}"
echo "REDIS_CONSUMER_NAME=${REDIS_CONSUMER_NAME}"
echo "SUPABASE_URL=${SUPABASE_URL}"
echo "SUPABASE_KEY=********" # No mostrar la clave por seguridad

echo ""
echo -e "${BLUE}=== INSTRUCCIONES PARA EJECUTAR LA PRUEBA COMPLETA ===${NC}"
echo -e "${YELLOW}Opción 1: Ejecutar los componentes en terminales separadas${NC}"
echo ""
echo -e "${GREEN}Terminal 1: Ejecutar el Comment Processor${NC}"
echo "cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "source integration_test/run_test_independiente_huracan_completo.sh"
echo "python processors/comment_processor/comment_processor.py"
echo ""
echo -e "${GREEN}Terminal 2: Ejecutar el Database Writer${NC}"
echo "cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "source integration_test/run_test_independiente_huracan_completo.sh"
echo "python processors/database_writer/database_writer.py"
echo ""
echo -e "${GREEN}Terminal 3: Ejecutar el YouTube Producer (o el script de prueba)${NC}"
echo "cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "source integration_test/run_test_independiente_huracan_completo.sh"
echo "# Para usar datos de prueba:"
echo "python integration_test/test_independiente_huracan.py"
echo "# O para conectarse a YouTube real:"
echo "python producers/youtube_producer/youtube_to_redis_producer.py"
echo ""
echo -e "${GREEN}Terminal 4: Verificar el almacenamiento en Supabase${NC}"
echo "cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "source integration_test/run_test_independiente_huracan_completo.sh"
echo "python integration_test/verify_supabase_storage.py"
echo ""

echo -e "${YELLOW}Opción 2: Ejecutar la prueba automática completa${NC}"
echo "cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "./integration_test/ejecutar_test_completo_con_db.sh"
echo ""

echo -e "${BLUE}Las variables de entorno están configuradas en esta terminal.${NC}"
echo -e "${BLUE}Puedes ejecutar cualquiera de los componentes desde aquí.${NC}"
echo -e "${BLUE}Si necesitas ayuda adicional, consulta GUIA_PRUEBAS_DATABASE_WRITER.md${NC}"
