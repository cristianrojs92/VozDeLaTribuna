# Procesador de Comentarios desde Redis

Este script actúa como un consumidor de un Stream de Redis, procesando los comentarios de transmisiones en vivo que fueron previamente ingeridos (por ejemplo, por el `youtube_to_redis_producer.py`).

## Funcionalidades (Versión MVP)

1.  **Conexión a Redis**: Se conecta a una instancia de Redis.
2.  **Grupo de Consumidores**: Utiliza un grupo de consumidores de Redis para leer mensajes de un stream específico de forma coordinada y robusta. Esto permite que múltiples instancias de este procesador puedan ejecutarse en paralelo, compartiendo la carga de trabajo sin procesar los mismos mensajes dos veces.
3.  **Deserialización**: Deserializa los mensajes (que se esperan en formato JSON) del stream.
4.  **Validación Básica**: Verifica la presencia de campos clave esperados en el mensaje.
5.  **Enriquecimiento Básico**:
    *   Añade un `internal_comment_id` (UUID v4) único para el sistema.
    *   Añade un `processing_timestamp_utc` que indica cuándo fue procesado el comentario.
    *   Realiza una limpieza simple del texto del comentario (`cleaned_text`).
6.  **Salida**: Imprime el diccionario del comentario enriquecido en la consola.

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

## Uso

1.  **Asegúrate de que tu servidor Redis esté corriendo** y que el stream (`REDIS_STREAM_NAME`) esté siendo alimentado con mensajes por un productor.

2.  **Ejecuta el Procesador:**
    Desde la carpeta `comment_processor` (y con el entorno virtual activado):
    ```bash
    python comment_processor.py
    ```

    El script comenzará a intentar leer y procesar mensajes del stream. Los comentarios enriquecidos se imprimirán en la consola.
    Para detener el script, presiona `Ctrl+C`.

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
  "cleaned_text": "contenido del comentario limpio..."
}
``` 