#!/bin/bash
# Script para ejecutar la prueba completa del procesador de comentarios
# Este script automatiza los pasos de la guía de solución
# Versión mejorada con mayor verbosidad en los logs

# Colores para los mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
function echo_step() {
  echo -e "${BLUE}==============================================================${NC}"
  echo -e "${BLUE}== $1${NC}"
  echo -e "${BLUE}==============================================================${NC}"
}

# Directorio raíz del proyecto
PROJECT_DIR="/Users/cristian/Proyectos/VozDeLaTribuna"
cd "$PROJECT_DIR" || { echo -e "${RED}Error: No se pudo acceder al directorio del proyecto${NC}"; exit 1; }

# Paso 1: Limpiar Redis
echo_step "PASO 1: Limpiando Redis"
python integration_test/clean_redis.py
if [ $? -ne 0 ]; then
  echo -e "${RED}Error al limpiar Redis. Abortando.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Redis limpiado correctamente${NC}\n"

# Paso 2: Configurar variables de entorno
echo_step "PASO 2: Configurando variables de entorno"
source integration_test/run_test_independiente_huracan.sh
echo -e "${GREEN}✓ Variables de entorno configuradas${NC}\n"

echo_step "INSTRUCCIONES FINALES"
echo -e "${YELLOW}AHORA DEBES EJECUTAR MANUALMENTE LOS SIGUIENTES PASOS EN TERMINALES SEPARADAS:${NC}\n"

echo -e "${GREEN}TERMINAL 1 - Ejecutar el procesador:${NC}"
echo -e "cd $PROJECT_DIR && source integration_test/run_test_independiente_huracan.sh && python processors/comment_processor/comment_processor.py\n"

echo -e "${GREEN}TERMINAL 2 - Ejecutar el script de prueba:${NC}"
echo -e "cd $PROJECT_DIR && source integration_test/run_test_independiente_huracan.sh && python integration_test/test_independiente_huracan.py\n"

echo -e "${CYAN}NOVEDADES EN LA VISUALIZACIÓN:${NC}"
echo -e "- Se han mejorado los logs para mostrar más información sobre el procesamiento"
echo -e "- Los comentarios procesados se mostrarán con más detalle en la consola"
echo -e "- Se incluyen emojis para facilitar la identificación de los diferentes tipos de mensajes:"
echo -e "  ${YELLOW}✅${NC} - Operación exitosa"
echo -e "  ${YELLOW}🔄${NC} - Procesando"
echo -e "  ${YELLOW}📦${NC} - Datos recibidos"
echo -e "  ${YELLOW}📝${NC} - Texto original"
echo -e "  ${YELLOW}🧹${NC} - Texto limpio"
echo -e "  ${YELLOW}😀${NC} - Sentimiento detectado"
echo -e "  ${YELLOW}⚽${NC} - Equipos mencionados"
echo -e "  ${YELLOW}👤${NC} - Jugadores mencionados"
echo -e "  ${YELLOW}📩${NC} - Mensaje recibido"
echo -e "  ${YELLOW}❌${NC} - Error o problema"

echo -e "\n${YELLOW}IMPORTANTE:${NC} Asegúrate de iniciar primero el procesador y esperar a que esté listo antes de ejecutar el script de prueba."
echo -e "El script de prueba verificará que el grupo de consumidores exista antes de enviar mensajes."
echo -e "\n${GREEN}¡Todo está listo para comenzar la prueba!${NC}" 