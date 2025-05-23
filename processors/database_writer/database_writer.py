import redis
import os
import json
import logging
import logging.handlers
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Crear carpeta de logs si no existe
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configurar el nombre del archivo de log con la fecha actual
current_date = datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join(log_dir, f"database_writer_{current_date}.log")

# Configurar logging con salida a consola y archivo
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[
                        # Handler para la consola
                        logging.StreamHandler(),
                        # Handler para archivo con rotación (5 archivos de 5MB máximo)
                        logging.handlers.RotatingFileHandler(
                            filename=log_file,
                            maxBytes=5*1024*1024,  # 5MB
                            backupCount=5,
                            encoding='utf-8'
                        )
                    ])

# Cargar variables de entorno
load_dotenv()

# Configuración de Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PROCESSED_STREAM = os.getenv('REDIS_PROCESSED_STREAM', 'comment_stream:processed')
REDIS_CONSUMER_GROUP = os.getenv('REDIS_CONSUMER_GROUP', 'database_writer_group')
REDIS_CONSUMER_NAME = os.getenv('REDIS_CONSUMER_NAME', f'db_writer_instance')

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Cuántos mensajes leer a la vez, y cuánto tiempo bloquear esperando nuevos mensajes
READ_COUNT = int(os.getenv('READ_COUNT', 10))
BLOCK_MILLISECONDS = int(os.getenv('BLOCK_MILLISECONDS', 2000))

def connect_to_redis():
    """Conecta a Redis y devuelve el cliente"""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()
        logging.info(f"Conectado a Redis: {REDIS_HOST}:{REDIS_PORT}")
        return client
    except Exception as e:
        logging.error(f"Error al conectar a Redis: {e}")
        return None

def connect_to_supabase():
    """Conecta a Supabase y devuelve el cliente"""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info(f"Conectado a Supabase: {SUPABASE_URL}")
        return client
    except Exception as e:
        logging.error(f"Error al conectar a Supabase: {e}")
        return None

def create_consumer_group(redis_client, stream_name, group_name):
    """Crea un grupo de consumidores en Redis si no existe"""
    try:
        redis_client.xgroup_create(stream_name, group_name, id='0', mkstream=True)
        logging.info(f"Grupo de consumidores creado: {group_name}")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logging.info(f"El grupo ya existe: {group_name}")
        else:
            logging.error(f"Error al crear grupo: {e}")
            raise

def store_comment(supabase_client, comment_data):
    """Almacena un comentario y sus datos relacionados en Supabase"""
    try:
        # 1. Primero buscar o crear el evento en la tabla events
        event_uuid = comment_data['event_uuid']
        
        # Buscar si el evento ya existe
        event_query = supabase_client.table('events').select('id').eq('event_uuid', event_uuid).execute()
        
        if event_query.data and len(event_query.data) > 0:
            # El evento ya existe, usar su ID
            event_id = event_query.data[0]['id']
            logging.debug(f"Evento encontrado con ID: {event_id}")
        else:
            # El evento no existe, crearlo
            match_context = comment_data.get('match_context', {})
            event_result = supabase_client.table('events').insert({
                'event_uuid': event_uuid,
                'stream_id': comment_data['stream_id'],
                'home_team': match_context.get('home_team'),
                'away_team': match_context.get('away_team'),
                'event_date': comment_data['capture_timestamp_utc']
            }).execute()
            
            if not event_result.data or len(event_result.data) == 0:
                logging.error(f"No se pudo crear el evento: {event_result}")
                return None
                
            event_id = event_result.data[0]['id']
            logging.info(f"Evento creado con ID: {event_id}")
        
        # 2. Insertar el comentario principal con la referencia al evento
        comment_result = supabase_client.table('comments').insert({
            'internal_comment_id': comment_data['internal_comment_id'],
            'source_comment_id': comment_data.get('source_comment_id'),
            'event_id': event_id,  # Usar el ID del evento, no el UUID
            'event_uuid': comment_data['event_uuid'],
            'stream_id': comment_data['stream_id'],
            'platform_source': comment_data['platform_source'],
            'author_display_name': comment_data.get('author_display_name'),
            'platform_author_id': comment_data.get('platform_author_id'),
            'original_text': comment_data['original_text'],
            'cleaned_text': comment_data['cleaned_text'],
            'sentiment_label': comment_data['sentiment_analysis']['label'],
            'sentiment_score': comment_data['sentiment_analysis']['score'],
            'capture_timestamp_utc': comment_data['capture_timestamp_utc'],
            'processing_timestamp_utc': comment_data['processing_timestamp_utc'],
            'home_team': comment_data.get('match_context', {}).get('home_team'),
            'away_team': comment_data.get('match_context', {}).get('away_team')
        }).execute()
        
        # Obtener el ID del comentario insertado
        if not comment_result.data or len(comment_result.data) == 0:
            logging.error(f"No se pudo obtener el ID del comentario insertado: {comment_result}")
            return None
            
        comment_id = comment_result.data[0]['id']
        logging.info(f"Comentario insertado con ID: {comment_id}")
        
        # 3. Insertar menciones de equipos
        for team in comment_data.get('mentioned_teams', []):
            try:
                team_result = supabase_client.table('mentioned_teams').insert({
                    'comment_id': comment_id,
                    'team_name': team['name']
                }).execute()
                logging.debug(f"Mención de equipo insertada: {team['name']}")
            except Exception as e:
                logging.error(f"Error al insertar mención de equipo {team['name']}: {e}")
        
        # 4. Insertar menciones de jugadores
        for player in comment_data.get('mentioned_players', []):
            try:
                player_result = supabase_client.table('mentioned_players').insert({
                    'comment_id': comment_id,
                    'player_name': player['name'],
                    'player_team': player['team']
                }).execute()
                logging.debug(f"Mención de jugador insertada: {player['name']} ({player['team']})")
            except Exception as e:
                logging.error(f"Error al insertar mención de jugador {player['name']}: {e}")
        
        logging.info(f"Comentario almacenado con éxito: {comment_id}")
        return comment_id
    except Exception as e:
        logging.error(f"Error al almacenar comentario: {e}")
        logging.error(f"Datos del comentario: {json.dumps(comment_data, indent=2)}")
        return None

def process_batch(redis_client, supabase_client):
    """Procesa un lote de mensajes del stream"""
    try:
        # Leer mensajes pendientes
        messages = redis_client.xreadgroup(
            groupname=REDIS_CONSUMER_GROUP,
            consumername=REDIS_CONSUMER_NAME,
            streams={REDIS_PROCESSED_STREAM: '>'},
            count=READ_COUNT,
            block=BLOCK_MILLISECONDS
        )
        
        if not messages:
            return 0
        
        count = 0
        success_count = 0
        ids_to_ack = []
        
        for stream_name, message_list in messages:
            logging.info(f"Recibidos {len(message_list)} mensajes para procesar")
            
            for message_id, message_data in message_list:
                try:
                    # Deserializar el payload del mensaje
                    comment_data = json.loads(message_data['payload'])
                    
                    # Almacenar en Supabase
                    comment_id = store_comment(supabase_client, comment_data)
                    
                    ids_to_ack.append(message_id)
                    count += 1
                    
                    if comment_id:
                        success_count += 1
                        logging.info(f"Comentario {count} procesado con éxito, ID en Supabase: {comment_id}")
                    else:
                        logging.warning(f"Comentario {count} procesado sin éxito (no se obtuvo ID)")
                        
                except json.JSONDecodeError as e:
                    logging.error(f"Error al decodificar JSON del mensaje {message_id}: {e}")
                    ids_to_ack.append(message_id)  # Aún así lo marcamos como procesado
                except Exception as e:
                    logging.error(f"Error procesando mensaje {message_id}: {e}")
                    # Añadir a ids_to_ack para evitar reprocesamiento infinito
                    ids_to_ack.append(message_id)
        
        # Confirmar procesamiento
        if ids_to_ack:
            ack_result = redis_client.xack(REDIS_PROCESSED_STREAM, REDIS_CONSUMER_GROUP, *ids_to_ack)
            logging.info(f"Confirmados {ack_result} mensajes de {len(ids_to_ack)} intentados")
        
        return success_count
    except redis.exceptions.RedisError as e:
        logging.error(f"Error de Redis en process_batch: {e}")
        return 0
    except Exception as e:
        logging.error(f"Error en process_batch: {e}")
        return 0

def main():
    """Función principal"""
    logging.info("🚀 Iniciando Database Writer para VozDeLaTribuna")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logging.error("❌ Falta configuración de Supabase. Revisa las variables SUPABASE_URL y SUPABASE_KEY en .env")
        return
    
    redis_client = connect_to_redis()
    if not redis_client:
        logging.error("❌ No se pudo conectar a Redis. Revisa las variables REDIS_HOST y REDIS_PORT en .env")
        return
        
    supabase_client = connect_to_supabase()
    if not supabase_client:
        logging.error("❌ No se pudo conectar a Supabase. Revisa las credenciales en .env")
        return
    
    try:
        create_consumer_group(redis_client, REDIS_PROCESSED_STREAM, REDIS_CONSUMER_GROUP)
        
        logging.info("✅ Iniciando procesamiento de comentarios y almacenamiento en Supabase")
        logging.info(f"👂 Escuchando stream: {REDIS_PROCESSED_STREAM}, grupo: {REDIS_CONSUMER_GROUP}")
        
        total_processed = 0
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                processed_count = process_batch(redis_client, supabase_client)
                total_processed += processed_count
                
                if processed_count > 0:
                    logging.info(f"✅ Ciclo {cycle_count}: Procesados {processed_count} comentarios. Total acumulado: {total_processed}")
                else:
                    if cycle_count % 10 == 0:  # Loggear solo cada 10 ciclos sin mensajes para reducir ruido
                        logging.info(f"😴 Ciclo {cycle_count}: Sin nuevos mensajes. Total acumulado: {total_processed}")
                    # Reducir carga en CPU cuando no hay mensajes
                    time.sleep(0.5)
            except Exception as e:
                logging.error(f"❌ Error en ciclo de procesamiento {cycle_count}: {e}")
                time.sleep(5)  # Esperar antes de reintentar
    except KeyboardInterrupt:
        logging.info("👋 Proceso interrumpido por el usuario. Total procesados: {total_processed}")
    except Exception as e:
        logging.error(f"❌ Error fatal: {e}")

if __name__ == "__main__":
    main()
