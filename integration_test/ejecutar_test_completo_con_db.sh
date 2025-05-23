#!/bin/bash
# ejecutar_test_completo_con_db.sh
# Script para ejecutar una prueba completa end-to-end incluyendo el almacenamiento en Supabase

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/cristian/Proyectos/VozDeLaTribuna"
LOG_DIR="$PROJECT_DIR/integration_test/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/test_completo_$TIMESTAMP.log"

# Crear directorio de logs si no existe
mkdir -p $LOG_DIR

# Función para mostrar mensajes
log_message() {
  local message="$1"
  local color="$2"
  echo -e "${color}${message}${NC}" | tee -a "$LOG_FILE"
}

# Iniciar log
log_message "=== PRUEBA COMPLETA END-TO-END: PROCESAMIENTO Y ALMACENAMIENTO ===" "$BLUE"
log_message "Fecha y hora: $(date)" "$BLUE"
log_message "Archivo de log: $LOG_FILE" "$BLUE"
log_message "===================================================================" "$BLUE"

# Verificar que Redis está en ejecución
log_message "\nVerificando que Redis está en ejecución..." "$YELLOW"
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_message "✅ Redis está en ejecución." "$GREEN"
else
    log_message "❌ Redis no está en ejecución. Por favor, inicia Redis antes de continuar." "$RED"
    log_message "Puedes iniciar Redis con: redis-server" "$YELLOW"
    exit 1
fi

# Limpiar Redis antes de comenzar
log_message "\nLimpiando Redis para comenzar con un entorno limpio..." "$YELLOW"
cd $PROJECT_DIR
python integration_test/clean_redis.py | tee -a "$LOG_FILE"

# Configurar todos los componentes para la prueba
log_message "\nConfigurando variables de entorno para todos los componentes..." "$YELLOW"
source integration_test/run_test_independiente_huracan_completo.sh

# Guardar las variables importantes para referencia en el log
log_message "\nVariables de entorno configuradas:" "$BLUE"
log_message "EVENT_UUID=$EVENT_UUID" "$BLUE"
log_message "MATCH_HOME_TEAM=$MATCH_HOME_TEAM" "$BLUE"
log_message "MATCH_AWAY_TEAM=$MATCH_AWAY_TEAM" "$BLUE"
log_message "REDIS_STREAM_NAME=$REDIS_STREAM_NAME" "$BLUE"
log_message "REDIS_PROCESSED_STREAM=$REDIS_PROCESSED_STREAM" "$BLUE"
log_message "SUPABASE_URL=$SUPABASE_URL" "$BLUE"

# Iniciar el Comment Processor en segundo plano
log_message "\nIniciando el Comment Processor en segundo plano..." "$YELLOW"
cd $PROJECT_DIR
python processors/comment_processor/comment_processor.py > "$LOG_DIR/comment_processor_$TIMESTAMP.log" 2>&1 &
COMMENT_PROCESSOR_PID=$!
log_message "✅ Comment Processor iniciado con PID $COMMENT_PROCESSOR_PID" "$GREEN"

# Esperar a que el Comment Processor esté listo
log_message "Esperando 5 segundos para que el Comment Processor se inicialice..." "$YELLOW"
sleep 5

# Verificar que el Comment Processor sigue en ejecución
if ps -p $COMMENT_PROCESSOR_PID > /dev/null; then
    log_message "✅ Comment Processor está en ejecución." "$GREEN"
else
    log_message "❌ Comment Processor no está en ejecución. Revisar los logs en $LOG_DIR/comment_processor_$TIMESTAMP.log" "$RED"
    exit 1
fi

# Iniciar el Database Writer en segundo plano
log_message "\nIniciando el Database Writer en segundo plano..." "$YELLOW"
cd $PROJECT_DIR
python processors/database_writer/database_writer.py > "$LOG_DIR/database_writer_$TIMESTAMP.log" 2>&1 &
DATABASE_WRITER_PID=$!
log_message "✅ Database Writer iniciado con PID $DATABASE_WRITER_PID" "$GREEN"

# Esperar a que el Database Writer esté listo
log_message "Esperando 5 segundos para que el Database Writer se inicialice..." "$YELLOW"
sleep 5

# Verificar que el Database Writer sigue en ejecución
if ps -p $DATABASE_WRITER_PID > /dev/null; then
    log_message "✅ Database Writer está en ejecución." "$GREEN"
else
    log_message "❌ Database Writer no está en ejecución. Revisar los logs en $LOG_DIR/database_writer_$TIMESTAMP.log" "$RED"
    exit 1
fi

# Ejecutar el script de prueba
log_message "\nEjecutando el script de prueba para enviar comentarios..." "$YELLOW"
cd $PROJECT_DIR
python integration_test/test_independiente_huracan.py | tee -a "$LOG_FILE"

# Esperar a que los comentarios sean procesados y almacenados
log_message "\nEsperando 10 segundos para que los comentarios sean procesados y almacenados..." "$YELLOW"
sleep 10

# Verificar el almacenamiento en Supabase
log_message "\nVerificando que los comentarios se almacenaron correctamente en Supabase..." "$YELLOW"
cd $PROJECT_DIR
python integration_test/verify_supabase_storage.py | tee -a "$LOG_FILE"

# Detener los procesos
log_message "\nDeteniendo procesos..." "$YELLOW"
kill $COMMENT_PROCESSOR_PID
kill $DATABASE_WRITER_PID

# Esperar a que los procesos terminen
sleep 2

# Verificar que los procesos terminaron
if ps -p $COMMENT_PROCESSOR_PID > /dev/null; then
    log_message "⚠️ Comment Processor (PID $COMMENT_PROCESSOR_PID) sigue en ejecución. Forzando terminación..." "$YELLOW"
    kill -9 $COMMENT_PROCESSOR_PID
fi

if ps -p $DATABASE_WRITER_PID > /dev/null; then
    log_message "⚠️ Database Writer (PID $DATABASE_WRITER_PID) sigue en ejecución. Forzando terminación..." "$YELLOW"
    kill -9 $DATABASE_WRITER_PID
fi

log_message "\n✅ Prueba completa finalizada." "$GREEN"
log_message "Los logs de los componentes están disponibles en:" "$BLUE"
log_message "- Log general: $LOG_FILE" "$BLUE"
log_message "- Comment Processor: $LOG_DIR/comment_processor_$TIMESTAMP.log" "$BLUE"
log_message "- Database Writer: $LOG_DIR/database_writer_$TIMESTAMP.log" "$BLUE"
log_message "\nRevisa los logs para verificar el correcto funcionamiento del sistema." "$BLUE"
