#!/bin/bash
# setup_and_run.sh
# Script para configurar y ejecutar los componentes de VozDeLaTribuna

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Configuración y Ejecución de VozDeLaTribuna ===${NC}"

# Verificar si Redis está en ejecución
echo -e "${YELLOW}Verificando si Redis está en ejecución...${NC}"
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Redis está en ejecución.${NC}"
else
    echo -e "${RED}Redis no está en ejecución. Por favor, inicia Redis antes de continuar.${NC}"
    echo -e "${YELLOW}Puedes iniciar Redis con: redis-server${NC}"
    exit 1
fi

# Crear directorios de logs si no existen
echo -e "${YELLOW}Creando directorios de logs...${NC}"
mkdir -p processors/comment_processor/logs
mkdir -p processors/database_writer/logs

# Verificar que existen los archivos .env
echo -e "${YELLOW}Verificando archivos de configuración...${NC}"
if [ ! -f processors/comment_processor/.env ]; then
    echo -e "${RED}No se encontró el archivo .env para el Comment Processor.${NC}"
    echo -e "${YELLOW}Creando .env a partir de .env.example...${NC}"
    cp processors/comment_processor/.env.example processors/comment_processor/.env
    echo -e "${GREEN}Archivo .env creado. Por favor, edítalo con tus configuraciones.${NC}"
fi

if [ ! -f processors/database_writer/.env ]; then
    echo -e "${RED}No se encontró el archivo .env para el Database Writer.${NC}"
    echo -e "${YELLOW}Creando .env a partir de .env.example...${NC}"
    cp processors/database_writer/.env.example processors/database_writer/.env
    echo -e "${GREEN}Archivo .env creado. Por favor, edítalo con tus configuraciones.${NC}"
fi

# Configurar entornos virtuales y dependencias
echo -e "${YELLOW}Configurando entornos virtuales...${NC}"

# Comment Processor
echo -e "${BLUE}Configurando Comment Processor...${NC}"
cd processors/comment_processor
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creando entorno virtual para Comment Processor...${NC}"
    python -m venv venv
fi
source venv/bin/activate
echo -e "${YELLOW}Instalando dependencias del Comment Processor...${NC}"
pip install -r requirements.txt
deactivate
cd ../..

# Database Writer
echo -e "${BLUE}Configurando Database Writer...${NC}"
cd processors/database_writer
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creando entorno virtual para Database Writer...${NC}"
    python -m venv venv
fi
source venv/bin/activate
echo -e "${YELLOW}Instalando dependencias del Database Writer...${NC}"
pip install -r requirements.txt
deactivate
cd ../..

echo -e "${GREEN}¡Configuración completada!${NC}"
echo -e "${BLUE}Para ejecutar los componentes:${NC}"
echo -e "${YELLOW}1. Comment Processor:${NC}"
echo -e "   cd processors/comment_processor"
echo -e "   source venv/bin/activate"
echo -e "   python comment_processor.py"
echo -e "${YELLOW}2. Database Writer:${NC}"
echo -e "   cd processors/database_writer"
echo -e "   source venv/bin/activate"
echo -e "   python database_writer.py"
echo -e "${YELLOW}3. YouTube Producer (opcional):${NC}"
echo -e "   cd producers/youtube_producer"
echo -e "   source venv/bin/activate"
echo -e "   python youtube_to_redis_producer.py"

echo -e "${GREEN}¡Listo para procesar comentarios!${NC}"
