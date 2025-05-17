import pytchat
import redis
import os
import time
import json
from datetime import datetime, timezone
import logging
from dotenv import load_dotenv
import uuid

# Configurar logging básico (en inglés para la salida estándar)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración --- (Nombres de variables en inglés)
EVENT_UUID_STR = os.getenv('EVENT_UUID')
YOUTUBE_VIDEO_ID = os.getenv('YOUTUBE_VIDEO_ID')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_STREAM_NAME = os.getenv('REDIS_STREAM_NAME', 'comment_stream:live')
# CAPTURE_INTERVAL_SECONDS está disponible si se necesita un sleep explícito más adelante
# CAPTURE_INTERVAL_SECONDS = float(os.getenv('CAPTURE_INTERVAL_SECONDS', 1))

def is_valid_uuid(uuid_to_test, version=4):
    """Valida si la cadena proporcionada es un UUID válido."""
    try:
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test # Comprueba que la cadena original sea igual a la representación canónica del UUID

def connect_to_redis(host, port):
    """Conecta a Redis y devuelve la instancia del cliente."""
    try:
        r = redis.Redis(host=host, port=port, db=0, decode_responses=False)
        r.ping()  # Verificar conexión
        logging.info(f"Successfully connected to Redis at {host}:{port}") # Log en inglés
        return r
    except redis.exceptions.ConnectionError as e:
        logging.error(f"Could not connect to Redis: {e}") # Log en inglés
        return None

def format_comment_to_dict(comment_data, event_uuid, stream_id):
    """Transforma el objeto de comentario de pytchat al formato de diccionario deseado (con claves en inglés)."""
    try:
        # comment_data.timestamp es una marca de tiempo epoch en milisegundos
        capture_datetime_utc = datetime.fromtimestamp(comment_data.timestamp / 1000.0, tz=timezone.utc)
        capture_timestamp_utc_str = capture_datetime_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' # Formato ISO 8601 UTC

        formatted_comment = {
            "event_uuid": str(event_uuid),
            "stream_id": str(stream_id),
            "platform_source": "youtube",
            "capture_timestamp_utc": capture_timestamp_utc_str,
            "author_display_name": str(comment_data.author.name),
            "original_text": str(comment_data.message),
            # Campos opcionales
            "source_comment_id": str(comment_data.id),
            "platform_author_id": str(comment_data.author.channelId)
        }
        return formatted_comment
    except Exception as e:
        comment_id_log = comment_data.id if hasattr(comment_data, 'id') else 'N/A' # Obtener ID para el log si existe
        logging.error(f"Error formatting comment {comment_id_log}: {e}") # Log en inglés
        return None

def capture_and_send_comments(event_uuid, video_id, redis_client, stream_name):
    """Captura comentarios de YouTube y los envía a un stream de Redis."""
    # Las validaciones de los parámetros requeridos se hacen antes de llamar a esta función

    logging.info(f"Starting comment capture for event UUID: {event_uuid}, video ID: {video_id}") # Log en inglés
    logging.info(f"Sending comments to Redis stream: {stream_name}") # Log en inglés

    try:
        chat_processor = pytchat.create(video_id=video_id)
        logging.info(f"Connected to YouTube chat for video: {video_id}") # Log en inglés

        while chat_processor.is_alive():
            livechat_data = chat_processor.get() # Obtiene un lote de datos del chat
            for comment_item in livechat_data.items: # Itera sobre los comentarios en el lote
                logging.debug(f"Comment received: Author: {comment_item.author.name}, Message: {comment_item.message}") # Log en inglés
                
                formatted_dict = format_comment_to_dict(comment_item, event_uuid, video_id)
                
                if formatted_dict:
                    try:
                        json_payload_str = json.dumps(formatted_dict) # Serializa el diccionario a una cadena JSON
                        # El ID del mensaje en el stream será generado automáticamente por Redis (*)
                        message_id = redis_client.xadd(stream_name, {'payload': json_payload_str})
                        log_msg_id = message_id.decode() if isinstance(message_id, bytes) else message_id # Decodifica si es bytes
                        logging.info(f"Comment sent to Redis (ID: {log_msg_id}): source_comment_id {formatted_dict['source_comment_id']}") # Log en inglés
                    except redis.exceptions.RedisError as e:
                        logging.error(f"Error sending comment {formatted_dict.get('source_comment_id', 'N/A')} to Redis: {e}") # Log en inglés
                    except json.JSONDecodeError as e:
                        logging.error(f"Error encoding comment to JSON {formatted_dict.get('source_comment_id', 'N/A')}: {e}") # Log en inglés
                else:
                    logging.warning(f"Comment skipped due to formatting error.") # Log en inglés
            
            # pytchat maneja su propio sondeo y espera.
            # Un sleep adicional puede ser útil para el control general del flujo si es necesario,
            # o para reducir la carga si el bucle interno de pytchat es demasiado rápido.
            # El método get() de pytchat puede ser bloqueante por un tiempo definido en su implementación.
            # time.sleep(CAPTURE_INTERVAL_SECONDS) # Descomentar si se necesita un control de ritmo más explícito

    except pytchat.exceptions.InvalidVideoIdException:
        logging.error(f"Invalid video ID: {video_id}") # Log en inglés
    except pytchat.exceptions.ChatUnavailable:
         logging.warning(f"Chat is not available for video {video_id} or has already ended. It might be an old video or not an active live stream.") # Log en inglés
    except KeyboardInterrupt:
        logging.info("Comment capture interrupted by user.") # Log en inglés
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True) # Log en inglés, exc_info para traceback
    finally:
        logging.info("Capture process finished.") # Log en inglés

if __name__ == "__main__":
    valid_config = True # Bandera para la validación de la configuración
    if not EVENT_UUID_STR:
        logging.error("Environment variable EVENT_UUID is not set. Please configure it.") # Log en inglés
        valid_config = False
    elif not is_valid_uuid(EVENT_UUID_STR):
        logging.error(f"EVENT_UUID '{EVENT_UUID_STR}' is not a valid UUID. Please provide a correct UUID v4.") # Log en inglés
        valid_config = False
        
    if not YOUTUBE_VIDEO_ID:
        logging.error("Environment variable YOUTUBE_VIDEO_ID is not set. Please configure it.") # Log en inglés
        valid_config = False

    if valid_config:
        redis_connection = connect_to_redis(REDIS_HOST, REDIS_PORT)
        if redis_connection:
            capture_and_send_comments(EVENT_UUID_STR, YOUTUBE_VIDEO_ID, redis_connection, REDIS_STREAM_NAME)
    else:
        logging.error("Script cannot start due to missing or invalid configuration. Please check environment variables.") # Log en inglés 