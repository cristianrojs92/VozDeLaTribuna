# Procesador de Comentarios desde Redis

Este script actúa como un consumidor de un Stream de Redis, procesando los comentarios de transmisiones en vivo que fueron previamente ingeridos (por ejemplo, por el `youtube_to_redis_producer.py`).

## Funcionalidades (Versión Actual)

1.  **Conexión a Redis**: Se conecta a una instancia de Redis.
2.  **Grupo de Consumidores**: Utiliza un grupo de consumidores de Redis para leer mensajes de un stream específico de forma coordinada y robusta. Esto permite que múltiples instancias de este procesador puedan ejecutarse en paralelo, compartiendo la carga de trabajo sin procesar los mismos mensajes dos veces.
3.  **Deserialización**: Deserializa los mensajes (que se esperan en formato JSON) del stream.
4.  **Validación Básica**: Verifica la presencia de campos clave esperados en el mensaje.
5.  **Enriquecimiento Completo**:
    *   Añade un `internal_comment_id` (UUID v4) único para el sistema.
    *   Añade un `processing_timestamp_utc` que indica cuándo fue procesado el comentario.
    *   Realiza una limpieza del texto del comentario (`cleaned_text`).
    *   Analiza el sentimiento del texto mediante diccionarios de palabras clave (`sentiment_analysis`).
    *   Detecta equipos mencionados en el comentario (`mentioned_teams`).
    *   Detecta jugadores mencionados en el comentario (`mentioned_players`).
    *   Añade contexto del partido en curso si está habilitado (`match_context`).
6.  **Manejo Robusto de Errores**:
    *   Cada componente del procesamiento está protegido con bloques try-except.
    *   Los errores no bloquean el proceso completo, permitiendo la continuidad del servicio.
    *   Se generan registros detallados de errores para facilitar la depuración.
7.  **Sistema de Logging Mejorado**:
    *   Utiliza emojis para mejorar la legibilidad de los registros 📋
    *   Cuenta mensajes procesados para mantener estadísticas de rendimiento
    *   Muestra resúmenes por lotes de mensajes procesados
    *   Niveles de logging configurables (INFO/DEBUG)
    *   Registro simultáneo en consola y archivos de log
    *   Rotación automática de archivos para gestionar el tamaño
8.  **Salida**: Imprime el diccionario del comentario enriquecido en la consola con formato JSON amigable.

## Configuración

1.  **Asegúrate de tener esta carpeta (`comment_processor`) en tu proyecto.**

2.  **Crear un Entorno Virtual (Recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar Dependencias:**
    Desde la carpeta `comment_processor`, ejecuta:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Variables de Entorno:**
    Copia el archivo `.env.example` a un nuevo archivo llamado `.env` dentro de esta misma carpeta (`comment_processor`):
    ```bash
    cp .env.example .env
    ```
    Edita el archivo `.env` y configura las siguientes variables:
    -   `REDIS_HOST`: El host de tu servidor Redis (por defecto: `localhost`).
    -   `REDIS_PORT`: El puerto de tu servidor Redis (por defecto: `6379`).
    -   `REDIS_STREAM_NAME`: El nombre del Stream en Redis del cual se consumirán los comentarios (por defecto: `comment_stream:live`). Debe coincidir con el stream al que escribe el productor.
    -   `REDIS_CONSUMER_GROUP_NAME`: Nombre del grupo de consumidores. Si no existe, el script intentará crearlo (por defecto: `comment_processing_group`).
    -   `REDIS_CONSUMER_NAME`: Un nombre único para esta instancia del consumidor dentro del grupo (por defecto: `processor_instance_1`).
    -   `READ_COUNT` (Opcional): Cuántos mensajes intentar leer del stream a la vez (por defecto: `10` en el script).
    -   `BLOCK_MILLISECONDS` (Opcional): Tiempo en milisegundos que el comando `XREADGROUP` esperará por nuevos mensajes si no hay ninguno disponible (por defecto: `2000` ms en el script).
    -   `MATCH_HOME_TEAM` (Opcional): El nombre del equipo local para el modo contextual (ejemplo: `"Independiente"`).
    -   `MATCH_AWAY_TEAM` (Opcional): El nombre del equipo visitante para el modo contextual (ejemplo: `"Huracán"`).
    -   `MATCH_CONTEXT_ENABLED` (Opcional): Si activar el modo de contexto de partido (`"true"` o `"false"`).

## Uso

1.  **Asegúrate de que tu servidor Redis esté corriendo** y que el stream (`REDIS_STREAM_NAME`) esté siendo alimentado con mensajes por un productor.

2.  **Ejecuta el Procesador:**
    Desde la carpeta `comment_processor` (y con el entorno virtual activado):
    ```bash
    python comment_processor.py
    ```

    El script comenzará a intentar leer y procesar mensajes del stream. Los comentarios enriquecidos se imprimirán en la consola.
    Para detener el script, presiona `Ctrl+C`.

## Sistema de Logs

El procesador ahora guarda todos los mensajes en archivos de log además de mostrarlos en la consola:

1. **Ubicación de los archivos**:
   - Los logs se guardan en la carpeta `logs` dentro del directorio del procesador
   - El nombre del archivo sigue el formato: `comment_processor_YYYY-MM-DD.log`

2. **Rotación de logs**:
   - Los archivos tienen un tamaño máximo de 5MB
   - Se mantienen hasta 5 archivos de respaldo (`.log.1`, `.log.2`, etc.)
   - Cuando el archivo actual supera el límite, se crea uno nuevo

3. **Acceso a los logs**:
   - Puedes ver los logs en tiempo real mientras se ejecuta el procesador:
     ```bash
     tail -f processors/comment_processor/logs/comment_processor_*.log
     ```
   - Para buscar información específica:
     ```bash
     grep "palabra clave" processors/comment_processor/logs/comment_processor_*.log
     ```

4. **Contenido de los logs**:
   - Todos los mensajes que se muestran en consola también se guardan en el archivo
   - Incluye marcas de tiempo, nivel de log y mensaje con emojis
   - Los comentarios procesados se guardan en formato JSON legible

## Estructura de Datos Esperada del Stream (Producida por `youtube_to_redis_producer.py`)

El procesador espera que cada mensaje en el stream de entrada (en el campo `payload`) sea una cadena JSON con la siguiente estructura (claves en inglés):

```json
{
  "event_uuid": "TU_EVENT_UUID_CONFIGURADO",
  "stream_id": "TU_YOUTUBE_VIDEO_ID_CONFIGURADO",
  "platform_source": "youtube",
  "capture_timestamp_utc": "YYYY-MM-DDTHH:MM:SS.sssZ",
  "author_display_name": "NombreDelAutor",
  "original_text": "Contenido del comentario.",
  "source_comment_id": "IDUnicoDelComentarioEnYouTube",
  "platform_author_id": "IDDelCanalDelAutorEnYouTube"
}
```

## Estructura de Datos de Salida (Comentario Enriquecido)

El comentario enriquecido impreso en la consola incluirá los campos originales más los siguientes añadidos por este procesador:

```json
{
  // ... campos originales ...
  "internal_comment_id": "UN_NUEVO_UUID_GENERADO_INTERNAMENTE",
  "processing_timestamp_utc": "YYYY-MM-DDTHH:MM:SS.sssZ", // Hora del procesamiento
  "cleaned_text": "contenido del comentario limpio...",
  "sentiment_analysis": {
    "label": "positive|negative|neutral",
    "score": 1.2 // Valor numérico que indica la intensidad del sentimiento
  },
  "mentioned_teams": [
    {"name": "Nombre Canónico del Equipo"}
  ],
  "mentioned_players": [
    {
      "name": "Nombre Canónico del Jugador",
      "team": "Equipo Actual del Jugador"
    }
  ],
  "match_context": {
    "home_team": "Equipo Local",
    "away_team": "Equipo Visitante"
  }
}
``` 

## Mejoras en el Logging y Visualización

El procesador ahora incluye un sistema de logging mejorado con emojis para facilitar la visualización:

- ✅ - Operación exitosa
- 🔄 - Procesamiento en curso
- 📦 - Datos recibidos
- 📝 - Texto original
- 🧹 - Texto limpio
- 😀 - Sentimiento detectado
- ⚽ - Equipos mencionados
- 👤 - Jugadores mencionados
- 📩 - Mensaje recibido
- ❌ - Error o problema
- 😴 - Esperando nuevos mensajes

También se muestran estadísticas de procesamiento, como:
- Total de mensajes procesados
- Total de mensajes fallidos
- Resúmenes por lotes de procesamiento 