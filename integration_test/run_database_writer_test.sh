#!/bin/bash
# run_database_writer_test.sh
# Configura el environment para las pruebas del Database Writer

echo "=== CONFIGURANDO ENTORNO PARA DATABASE WRITER ==="

# Variables de entorno para el Database Writer
export REDIS_HOST="localhost"
export REDIS_PORT=6379
export REDIS_PROCESSED_STREAM="comment_stream:processed"
export REDIS_CONSUMER_GROUP="database_writer_group"
export REDIS_CONSUMER_NAME="db_writer_test_instance"

# Variables de Supabase (usar los valores reales en entorno de prueba)
export SUPABASE_URL="https://cxnqyytqsnjcmpbijczp.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4bnF5eXRxc25qY21wYmlqY3pwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5ODY1MjYsImV4cCI6MjA2MzU2MjUyNn0.0AmNIoJ8rSpvtxGWgkWaJPGl14vxhkqndNWjcD_UmkA"

echo ""
echo "Variables de entorno configuradas:"
echo "REDIS_HOST=${REDIS_HOST}"
echo "REDIS_PORT=${REDIS_PORT}"
echo "REDIS_PROCESSED_STREAM=${REDIS_PROCESSED_STREAM}"
echo "REDIS_CONSUMER_GROUP=${REDIS_CONSUMER_GROUP}"
echo "REDIS_CONSUMER_NAME=${REDIS_CONSUMER_NAME}"
echo "SUPABASE_URL=${SUPABASE_URL}"
echo "SUPABASE_KEY=********" # No mostrar la clave por seguridad

echo ""
echo "=== INSTRUCCIONES ==="
echo "1. Primero, asegúrate de que el Comment Processor esté configurado y ejecutándose:"
echo "   cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "   source integration_test/run_test_independiente_huracan.sh"
echo "   python processors/comment_processor/comment_processor.py"
echo ""
echo "2. En otra terminal, ejecuta el Database Writer:"
echo "   cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "   source integration_test/run_database_writer_test.sh"
echo "   python processors/database_writer/database_writer.py"
echo ""
echo "3. En una tercera terminal, ejecuta el script de prueba:"
echo "   cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "   source integration_test/run_test_independiente_huracan.sh"
echo "   python integration_test/test_independiente_huracan.py"
echo ""
echo "4. Para verificar los datos en Supabase, usa el script de verificación:"
echo "   cd /Users/cristian/Proyectos/VozDeLaTribuna"
echo "   python integration_test/verify_supabase_storage.py"
echo ""
echo "Las variables de entorno están configuradas en esta terminal."
