# Productor de Comentarios de YouTube a Redis

Este script captura comentarios en tiempo real de una transmisión en vivo de YouTube y los envía a un Stream de Redis para su posterior procesamiento.

## Configuración

1.  **Clonar el repositorio (si aplica) o asegurarse de tener esta carpeta.**

2.  **Crear un Entorno Virtual (Recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar Dependencias:**
    Asegúrate de tener `pip` instalado. Desde la carpeta `youtube_producer`, ejecuta:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Variables de Entorno:**
    Copia el archivo `.env.example` a un nuevo archivo llamado `.env` dentro de esta misma carpeta (`youtube_producer`):
    ```bash
    cp .env.example .env
    ```
    Edita el archivo `.env` y configura las siguientes variables:
    -   `EVENT_UUID`: (Obligatorio) Un UUID (versión 4) único para identificar el evento específico (ej: un partido de fútbol particular). Ejemplo: `a1b2c3d4-e5f6-7890-1234-567890abcdef`.
    -   `YOUTUBE_VIDEO_ID`: (Obligatorio) El ID del video de YouTube del cual se leerán los comentarios. Es la parte final de la URL de un video (ej: `dQw4w9WgXcQ` para `https://www.youtube.com/watch?v=dQw4w9WgXcQ`).
    -   `REDIS_HOST`: El host donde se está ejecutando tu servidor Redis (por defecto: `localhost`).
    -   `REDIS_PORT`: El puerto de tu servidor Redis (por defecto: `6379`).
    -   `REDIS_STREAM_NAME`: El nombre del Stream en Redis donde se publicarán los comentarios (por defecto: `comment_stream:live`).
    -   `CAPTURE_INTERVAL_SECONDS` (Opcional): Intervalo en segundos para esperar entre la finalización de un ciclo de obtención de mensajes y el inicio del siguiente. `pytchat` maneja su propio ritmo de sondeo interno. Este script actualmente no utiliza un `time.sleep()` explícito en el bucle principal de `pytchat`, pero la variable está disponible si se quisiera reintroducir.

## Uso

1.  **Asegúrate de que tu servidor Redis esté corriendo y sea accesible** con la configuración proporcionada en el archivo `.env`.

2.  **Ejecuta el Productor:**
    Desde la carpeta `youtube_producer` (y con el entorno virtual activado si lo creaste):
    ```bash
    python youtube_to_redis_producer.py
    ```

    El script comenzará a registrar su actividad en la consola, incluyendo la conexión a YouTube, la recepción de comentarios y su envío a Redis.

## Estructura de Datos en Redis

Los comentarios se envían al Stream de Redis especificado por `REDIS_STREAM_NAME`. Cada mensaje en el Stream contendrá un único campo llamado `payload`, y su valor será una cadena JSON con la siguiente estructura (las claves están en inglés):

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

## Manejo de Errores

El script incluye logging básico para informar sobre el proceso y posibles errores (ej: problemas de conexión a Redis, ID de video inválido, chat no disponible). Puedes detener el script manualmente con `Ctrl+C`. 