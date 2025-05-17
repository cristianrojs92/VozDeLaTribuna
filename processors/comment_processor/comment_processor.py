import redis
import os
import time
import json
import uuid # Para generar internal_comment_id
from datetime import datetime, timezone
import logging
import re # Para la limpieza de texto
from dotenv import load_dotenv

# Configurar logging básico (salida en inglés)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración --- (Nombres de variables en inglés)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_STREAM_NAME = os.getenv('REDIS_STREAM_NAME', 'comment_stream:live')
REDIS_CONSUMER_GROUP_NAME = os.getenv('REDIS_CONSUMER_GROUP_NAME', 'comment_processing_group')
REDIS_CONSUMER_NAME = os.getenv('REDIS_CONSUMER_NAME', f'processor_instance_{uuid.uuid4().hex[:6]}') # Nombre de consumidor único por defecto

# Cuántos mensajes leer a la vez, y cuánto tiempo bloquear esperando nuevos mensajes
READ_COUNT = int(os.getenv('READ_COUNT', 10))
BLOCK_MILLISECONDS = int(os.getenv('BLOCK_MILLISECONDS', 2000))

# Campos esperados en el JSON del payload del stream
EXPECTED_FIELDS = [
    "event_uuid", "stream_id", "platform_source", 
    "capture_timestamp_utc", "author_display_name", "original_text",
    "source_comment_id", "platform_author_id"
]

def connect_to_redis(host, port):
    """Conecta a Redis y devuelve la instancia del cliente."""
    try:
        r = redis.Redis(host=host, port=port, db=0, decode_responses=True) # decode_responses=True para obtener strings
        r.ping()  # Verificar conexión
        logging.info(f"Successfully connected to Redis at {host}:{port}")
        return r
    except redis.exceptions.ConnectionError as e:
        logging.error(f"Could not connect to Redis: {e}")
        return None

def create_consumer_group_if_not_exists(redis_client, stream_name, group_name):
    """Intenta crear el grupo de consumidores si no existe."""
    try:
        # MKSTREAM=True crea el stream si no existe, junto con el grupo
        redis_client.xgroup_create(name=stream_name, groupname=group_name, id='0', mkstream=True)
        logging.info(f"Consumer group '{group_name}' created for stream '{stream_name}'.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logging.info(f"Consumer group '{group_name}' already exists for stream '{stream_name}'.")
        else:
            logging.error(f"Error creating/checking consumer group '{group_name}': {e}")
            raise # Relanzar la excepción si es algo diferente a que ya existe

def clean_text(input_text):
    """Realiza una limpieza básica del texto."""
    if not isinstance(input_text, str):
        return "" # Devolver cadena vacía si no es string
    text = input_text.lower() # Convertir a minúsculas
    text = re.sub(r'\s+', ' ', text).strip() # Reemplazar múltiples espacios con uno solo y quitar espacios al inicio/final
    # Aquí se podrían añadir más reglas de limpieza (ej. remover emojis, URLs, etc.)
    return text

def process_message(message_id, message_data):
    """Procesa un único mensaje del stream: deserializa, valida y enriquece."""
    try:
        # El payload del mensaje es una cadena JSON
        comment_payload_str = message_data.get('payload')
        if not comment_payload_str:
            logging.warning(f"Message {message_id} has no 'payload' field. Skipping.")
            return None

        comment_dict = json.loads(comment_payload_str)

        # Validar campos esperados
        missing_fields = [field for field in EXPECTED_FIELDS if field not in comment_dict]
        if missing_fields:
            logging.warning(f"Message {message_id} (source_comment_id: {comment_dict.get('source_comment_id', 'N/A')}) is missing fields: {missing_fields}. Skipping.")
            return None

        # Enriquecimiento
        comment_dict["internal_comment_id"] = str(uuid.uuid4())
        comment_dict["processing_timestamp_utc"] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        comment_dict["cleaned_text"] = clean_text(comment_dict.get("original_text"))
        
        # Aquí se añadirían más pasos de enriquecimiento en el futuro (sentimiento, NER, etc.)

        logging.info(f"Successfully processed message {message_id} (internal_id: {comment_dict['internal_comment_id']})")
        return comment_dict

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON for message {message_id}: {e}. Payload: {comment_payload_str[:200]}... Skipping.")
        return None
    except Exception as e:
        logging.error(f"Unexpected error processing message {message_id}: {e}", exc_info=True)
        return None

def consume_and_process_comments(redis_client, stream_name, group_name, consumer_name):
    """Bucle principal para consumir y procesar comentarios del stream de Redis."""
    logging.info(f"Starting consumer '{consumer_name}' for group '{group_name}' on stream '{stream_name}'. Waiting for messages...")

    while True:
        try:
            # Leer mensajes del stream para este consumidor y grupo
            # '>' significa leer mensajes nuevos que no han sido entregados a otros consumidores del grupo
            messages = redis_client.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: '>'}, # El '>' es para mensajes nuevos
                count=READ_COUNT,
                block=BLOCK_MILLISECONDS
            )

            if not messages:
                # No hay mensajes nuevos después del tiempo de bloqueo, el bucle continúa y reintenta
                logging.debug("No new messages received, continuing to listen...")
                continue

            # messages es una lista de tuplas: [(stream_name, [(message_id, message_data_dict)])]
            for stream, message_list in messages:
                message_ids_to_ack = []
                for message_id, message_data in message_list:
                    logging.debug(f"Received message {message_id} from stream {stream.decode() if isinstance(stream, bytes) else stream}")
                    
                    enriched_comment = process_message(message_id, message_data)

                    if enriched_comment:
                        # Por ahora, solo imprimir el comentario enriquecido
                        # En el futuro, esto podría enviarse a otro stream, base de datos, WebSocket, etc.
                        print(json.dumps(enriched_comment, indent=2, ensure_ascii=False))
                        message_ids_to_ack.append(message_id)
                    else:
                        # Si process_message devuelve None, significa que el mensaje no se pudo procesar o se omitió.
                        # Podríamos decidir si hacer ACK de todas formas para quitarlo de la cola de pendientes (PEL)
                        # o dejarlo para una futura inspección/reintento manual.
                        # Por simplicidad MVP, si no se procesa bien, no se hace ACK explícito aquí, 
                        # pero tampoco se reintenta automáticamente en este bucle.
                        # Un mensaje no procesado y sin ACK permanecerá en la PEL (Pending Entries List)
                        # hasta que sea reclamado o se haga ACK de alguna forma.
                        # Para el MVP, asumimos que si hay un error grave, se registra y el mensaje se omite.
                        # Si el mensaje fue simplemente "omitido" por una validación fallida, aún es bueno hacer ACK.
                        # Modificación: Haremos ACK incluso si se omite por validación para no dejarlo pendiente.
                        if message_data.get('payload'): # Solo si hubo payload para intentar procesar
                             message_ids_to_ack.append(message_id)

                if message_ids_to_ack:
                    # Acusar recibo de los mensajes procesados (o conscientemente omitidos)
                    ack_result = redis_client.xack(stream_name, group_name, *message_ids_to_ack)
                    logging.info(f"Acknowledged {ack_result} messages: {message_ids_to_ack}")

        except redis.exceptions.RedisError as e:
            logging.error(f"Redis error during consumption loop: {e}. Attempting to reconnect in 5s...")
            time.sleep(5)
            # Podríamos intentar reconectar aquí, pero por simplicidad, si la conexión se pierde de forma crítica,
            # el script podría necesitar reiniciarse. La librería redis-py maneja algunas reconexiones.
        except KeyboardInterrupt:
            logging.info("Consumer process interrupted by user. Exiting...")
            break
        except Exception as e:
            logging.error(f"Unexpected error in consumer loop: {e}", exc_info=True)
            # Esperar un poco antes de reintentar para evitar un bucle apretado en caso de errores persistentes
            time.sleep(5)

if __name__ == "__main__":
    redis_conn = connect_to_redis(REDIS_HOST, REDIS_PORT)

    if redis_conn:
        try:
            create_consumer_group_if_not_exists(redis_conn, REDIS_STREAM_NAME, REDIS_CONSUMER_GROUP_NAME)
            consume_and_process_comments(redis_conn, REDIS_STREAM_NAME, REDIS_CONSUMER_GROUP_NAME, REDIS_CONSUMER_NAME)
        except Exception as e:
            logging.critical(f"Failed to initialize or run consumer: {e}", exc_info=True)
    else:
        logging.critical("Could not connect to Redis. Exiting processor.") 