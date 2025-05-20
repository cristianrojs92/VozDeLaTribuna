# Voz De La Tribuna

Sistema de procesamiento en tiempo real de comentarios deportivos para analizar sentimientos, detectar menciones de equipos y jugadores.

## Estructura del Proyecto

- **processors/**: Procesadores de mensajes
  - **comment_processor/**: Procesador principal de comentarios con análisis de sentimientos
- **producers/**: Productores que envían mensajes a Redis
  - **youtube_producer/**: Productor que captura comentarios de YouTube Live
- **integration_test/**: Pruebas de integración del sistema
- **data/**: Diccionarios y datos estructurados
  - **dictionaries/**: Diccionarios de equipos y jugadores
- **scraper-promiedos/**: Herramientas para recopilar datos deportivos

## Configuración de Git

Este proyecto utiliza archivos `.gitignore` y `.gitattributes` para gestionar los archivos que deben ser incluidos en el control de versiones.

### Archivos Ignorados

Los siguientes tipos de archivos son ignorados automáticamente:

- **Archivos de entorno**: `.env` (excepto los ejemplos `.env.example`)
- **Logs**: Todos los archivos `.log` y directorios `logs/`
- **Entornos virtuales**: `venv/`, `.venv/`, `env/`
- **Cache y archivos compilados**: `__pycache__/`, `.pyc`, etc.
- **Archivos temporales**: `.tmp`, `.bak`, etc.
- **Datos generados**: Salidas específicas de cada componente

### Trabajo con archivos sensibles

Para archivos con credenciales o configuraciones locales:

1. Usa los archivos `.env.example` como plantilla
2. Copia a un archivo `.env` local (que será ignorado por Git)
3. Añade tus credenciales y configuraciones específicas

## Configuración del Entorno

1. Clona este repositorio:
   ```bash
   git clone https://[url-del-repositorio]/VozDeLaTribuna.git
   cd VozDeLaTribuna
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. Instala las dependencias para el componente que desees utilizar:
   ```bash
   cd processors/comment_processor
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno:
   ```bash
   cp .env.example .env
   # Edita el archivo .env con tus configuraciones
   ```

## Ejecución de Componentes

Consulta el README.md dentro de cada directorio para instrucciones específicas de cada componente. 