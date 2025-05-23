#!/bin/bash
# test_master.sh
# Script maestro para elegir y ejecutar diferentes tipos de pruebas

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/cristian/Proyectos/VozDeLaTribuna"
cd $PROJECT_DIR

clear
echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}      SISTEMA DE PRUEBAS VOZ DE LA TRIBUNA    ${NC}"
echo -e "${BLUE}==============================================${NC}"
echo ""
echo -e "${YELLOW}Selecciona el tipo de prueba que deseas ejecutar:${NC}"
echo ""
echo -e "${GREEN}1. Prueba con datos simulados${NC}"
echo "   Utiliza datos de prueba predefinidos para simular comentarios"
echo "   del partido Independiente vs Huracán."
echo ""
echo -e "${GREEN}2. Prueba con YouTube en vivo${NC}"
echo "   Conecta con un video en vivo de YouTube para capturar comentarios"
echo "   reales. Requiere configurar el ID del video."
echo ""
echo -e "${GREEN}3. Prueba manual de componentes individuales${NC}"
echo "   Configura el entorno pero permite ejecutar cada componente"
echo "   por separado para pruebas detalladas."
echo ""
echo -e "${GREEN}4. Limpiar entorno de pruebas${NC}"
echo "   Elimina streams y grupos de consumidores de Redis para iniciar"
echo "   pruebas desde cero."
echo ""
echo -e "${GREEN}0. Salir${NC}"
echo ""
echo -e "${YELLOW}Ingresa el número de la opción deseada:${NC} "
read option

case $option in
    1)
        echo -e "${BLUE}Ejecutando prueba con datos simulados...${NC}"
        ./integration_test/ejecutar_test_completo_con_db.sh
        ;;
    2)
        echo -e "${YELLOW}Para esta prueba, necesitas el ID de un video en vivo de YouTube.${NC}"
        echo -e "${YELLOW}Puedes obtenerlo de la URL del video (ej: dQw4w9WgXcQ).${NC}"
        echo -e "${YELLOW}Ingresa el ID del video de YouTube:${NC} "
        read youtube_id
        
        if [ -z "$youtube_id" ]; then
            echo -e "${RED}No se proporcionó un ID de video. Utilizando ID de ejemplo.${NC}"
            youtube_id="l5JICYBZUQw"
        fi
        
        # Crear un script temporal con el ID de YouTube configurado
        temp_script="/tmp/run_youtube_test_$$.sh"
        cp integration_test/run_test_independiente_huracan_completo.sh $temp_script
        sed -i '' "s/export YOUTUBE_VIDEO_ID=\".*\"/export YOUTUBE_VIDEO_ID=\"$youtube_id\"/" $temp_script
        chmod +x $temp_script
        
        echo -e "${BLUE}Configurando entorno para prueba con YouTube en vivo...${NC}"
        source $temp_script
        
        echo -e "${BLUE}Iniciando componentes...${NC}"
        # Iniciar el Comment Processor en segundo plano
        python processors/comment_processor/comment_processor.py > /tmp/comment_processor_$$.log 2>&1 &
        comment_processor_pid=$!
        echo -e "${GREEN}Comment Processor iniciado con PID $comment_processor_pid${NC}"
        
        # Iniciar el Database Writer en segundo plano
        python processors/database_writer/database_writer.py > /tmp/database_writer_$$.log 2>&1 &
        database_writer_pid=$!
        echo -e "${GREEN}Database Writer iniciado con PID $database_writer_pid${NC}"
        
        # Iniciar el YouTube Producer en primer plano para ver los comentarios
        echo -e "${BLUE}Iniciando YouTube Producer para el video ID: $youtube_id${NC}"
        echo -e "${BLUE}Presiona Ctrl+C para detener la captura cuando desees.${NC}"
        python producers/youtube_producer/youtube_to_redis_producer.py
        
        # Cuando el usuario presiona Ctrl+C, detenemos los procesos en segundo plano
        echo -e "${YELLOW}Deteniendo componentes...${NC}"
        kill $comment_processor_pid
        kill $database_writer_pid
        
        # Verificar los datos en Supabase
        echo -e "${BLUE}Verificando datos almacenados en Supabase...${NC}"
        python integration_test/verify_supabase_storage.py
        
        # Limpiar
        rm $temp_script
        ;;
    3)
        echo -e "${BLUE}Configurando entorno para prueba manual...${NC}"
        source integration_test/run_test_independiente_huracan_completo.sh
        echo -e "${GREEN}Entorno configurado.${NC}"
        echo -e "${YELLOW}Ahora puedes ejecutar cada componente en terminales separadas siguiendo las instrucciones.${NC}"
        ;;
    4)
        echo -e "${BLUE}Limpiando entorno de pruebas...${NC}"
        python integration_test/clean_redis.py
        ;;
    0)
        echo -e "${BLUE}Saliendo del sistema de pruebas.${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Opción no válida.${NC}"
        ;;
esac

echo -e "${BLUE}==============================================${NC}"
echo -e "${GREEN}Operación completada.${NC}"
echo -e "${BLUE}==============================================${NC}"
