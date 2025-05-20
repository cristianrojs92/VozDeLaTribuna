import redis
import os
import time
import json
import uuid # Para generar internal_comment_id
from datetime import datetime, timezone
import logging
import re # Para la limpieza de texto
from dotenv import load_dotenv
import glob # Para buscar archivos JSON de jugadores

# Configurar logging básico (salida en inglés)
# Aumentar el nivel de detalle del logging para asegurar que se muestren todos los mensajes
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración Específica del Partido ---
# Obtener equipos específicos para el partido actual desde variables de entorno
MATCH_HOME_TEAM = os.getenv('MATCH_HOME_TEAM', '')
MATCH_AWAY_TEAM = os.getenv('MATCH_AWAY_TEAM', '')
MATCH_CONTEXT_ENABLED = os.getenv('MATCH_CONTEXT_ENABLED', 'true').lower() == 'true'

# --- Diccionarios para Análisis de Sentimiento MVP ---
DICCIONARIO_POSITIVAS_MVP = {
    # Festejo y Alegría General
    "gol": 1.0, "gool": 1.0, "goool": 1.0, "golazo": 1.8, "golazooo": 1.8, "victoria": 1.5,
    "ganamos": 1.4, "ganar": 1.2, "triunfo": 1.5, "partidazo": 1.6, "alegria": 1.0, "felicidad": 1.0,
    "festejo": 0.9, "que grande": 1.2, "qué grande": 1.2, "que bueno": 1.1, "qué bueno": 1.1,
    "buenisimo": 1.3, "buenísima": 1.3, "joya": 1.0, "espectacular": 1.5, "impresionante": 1.6,
    "épico": 1.7, "epico": 1.7,
    # Elogios a Jugadores/Equipo
    "crack": 1.7, "genio": 1.6, "figura": 1.5, "idolo": 1.6, "ídolo": 1.6, "maestro": 1.4,
    "jugadorazo": 1.7, "equipazo": 1.6, "la rompio": 1.5, "la rompió": 1.5, "se paso": 1.4,
    "se pasó": 1.4, "te pusiste la 10": 2.0, "pusiste la 10": 2.0, "jugador": 0.5,
    "maquina": 1.3, "máquina": 1.3, "bestia": 1.4, "mostro": 1.3, "monstruo": 1.3,
    # Apoyo y Ánimo
    "vamos": 0.8, "vamooos": 0.8, "vamo": 0.8, "dale": 0.7, "dalee": 0.7, "aguante": 0.9,
    "fuerza": 0.6, "con todo": 0.8, "a full": 0.7, "huevo": 1.0, "huevos": 1.0,
    "pongan huevo": 0.8,
    # Buen Rendimiento o Calidad
    "bien": 0.9, "muy bien": 1.2, "excelente": 1.5, "buen partido": 1.1, "buena jugada": 1.0,
    "calidad": 1.2, "jugaron bien": 1.1, "agrandado": 0.7, "comerse la cancha": 1.6,
    "mortal": 1.4, "que jugador": 1.5, "qué jugador": 1.5, "que gol": 1.3, "qué gol": 1.3,
    "merecido": 1.0, "justicia": 0.8,
    # Emojis Positivos
    "👍": 1.0, "❤️": 1.2, "🎉": 1.1, "😂": 0.7, "👏": 0.9, "🔥": 1.3, "⚽": 0.5,
    "🏆": 1.4, "💪": 0.8, "💯": 1.2, "🤩": 1.3, "🥳": 1.1,
    # Nuevas adiciones basadas en análisis de comentarios
    "ufff": 0.7, "uf": 0.7, "uff": 0.7, "god": 1.8, "goddd": 1.8, "joyita": 1.1,
    "claro": 0.6, "claro que si": 0.7, "obvio": 0.6, "banco": 1.2, "te banco": 1.3,
    "bancan": 1.2, "🤑": 1.0, "sacalaaa": 0.9,
    # Términos adicionales basados en análisis de comentarios de fútbol 
    "increíble": 1.5, "increible": 1.5, "comiendo la cancha": 1.5, "se come la cancha": 1.5,
    "imparable": 1.4, "gran partido": 1.4, "gran atajada": 1.3, "salvó": 1.2, "salva": 1.2,
    "salvando": 1.2, "con calidad": 1.1, "atajada": 1.0, "tiene nivel": 1.0, "dominan": 0.9,
    "dominando": 0.9, "preciso": 0.9, "precisa": 0.9, "presiona": 0.8, "presionando": 0.8,
    "bien ubicado": 0.8, "recupera": 0.8, "metido": 0.8, "concentrado": 0.8, "atento": 0.7,
    "anticipando": 0.7, "intenta": 0.6,
    # Nuevos términos de posesión de balón (añadidos para corregir clasificación)
    "dominar": 1.2, "domina": 1.2, "dominan": 1.2, "posesión": 0.9, "posesion": 0.9,
    "tiene la pelota": 1.0, "tienen la pelota": 1.0, "maneja el balón": 1.1, "manejan el balón": 1.1,
    "controla el partido": 1.3, "controlan el partido": 1.3, "diablos rojos dominan": 1.5,
    "dominar la posesión": 1.4, "domina la posesión": 1.4, "dominan la posesión": 1.4,
    "dominar la posesion": 1.4, "domina la posesion": 1.4, "dominan la posesion": 1.4,
    "buen manejo": 1.1, "retiene el balón": 0.9, "retienen el balón": 0.9,
    "retiene la pelota": 0.9, "retienen la pelota": 0.9, "toque": 0.8, "toques": 0.8,
    "buen toque": 1.0, "buenos toques": 1.0, "circulación": 0.9, "circulacion": 0.9,
    "buena circulación": 1.1, "buena circulacion": 1.1, "control del balón": 1.0, "control del balon": 1.0
}

DICCIONARIO_NEGATIVAS_MVP = {
    "pecho frío": -1.8, "burro": -1.3, "morfón": -1.6, "amargo": -1.5,
    "cabaret": -1.2, "abandonamos": -1.3, "equipo sin alma": -1.6,
    "cagón": -1.7, "ladrones": -1.6, "chorros": -1.6,
    "nos robaron": -1.7, "vendehumo": -1.5, "horrible": -1.4,
    "sin huevos": -1.5, "asco": -1.6, "desastre": -1.5,
    "muertos": -1.6, "dan lástima": -1.5, "sin actitud": -1.3,
    "no se puede creer": -1.1, "regalamos el partido": -1.4,
    "desastroso": -1.5, "impresentable": -1.5, "sos un fantasma": -1.4,
    "le quedó grande": -1.3
}

PALABRAS_NEGACION_MVP = ["no", "ni", "nunca", "jamas", "jamás", "tampoco", "sin", "nadie"]

# --- Diccionario para Detección de Equipos MVP ---
EQUIPOS_MVP_COMPLETO = {
    "River Plate": ["river", "millo", "millonarios", "gallina", "gallinas", "la banda", "el más grande", "carp"],
    "Boca Juniors": ["boca", "xeneize", "bostero", "bosteros", "azul y oro", "la mitad más uno", "cabj"],
    "Independiente": ["independiente", "el rojo", "diablos rojos", "rey de copas", "orgullo nacional", "independiente de américa"],
    "Racing Club": ["racing", "la academia", "el primer grande"],
    "San Lorenzo de Almagro": ["san lorenzo", "ciclón", "cuervo", "los cuervos", "santos", "azulgrana", "matadores", "gauchos de boedo", "el gigante de boedo"],
    "Club Atlético Güemes": ["güemes", "club atlético güemes", "gauchos azulgranas", "los gauchos", "azulgranas", "guemes"],
    "Quilmes Atlético Club": ["quilmes", "quilmes atlético club", "el cervecero", "cervecero", "los cerveceros", "decano", "qac"],
    "Estudiantes de La Plata": ["estudiantes", "estudiantes lp", "pincha", "pincharrata", "león"],
    "Gimnasia y Esgrima La Plata": ["gimnasia", "gimnasia lp", "gelp", "el lobo", "lobo", "tripero", "triperos", "basurero", "mens sana"],
    "Vélez Sarsfield": ["vélez", "velez", "el fortín", "la v azulada", "fortineros"],
    "Huracán": ["huracán", "el globo", "globito", "quemero"],
    "Newell's Old Boys": ["newell's", "newells", "nob", "la lepra", "leprosos"],
    "Rosario Central": ["rosario central", "central", "canalla", "canayas", "la academia rosarina", "auriazul", "los auriazules"],
    "Lanús": ["lanús", "lanus", "granate", "los globetrotters", "los albañiles"],
    "Banfield": ["banfield", "el taladro", "la banda del sur"],
    "Argentinos Juniors": ["argentinos juniors", "argentinos", "aaaj", "el bicho", "bichitos colorados", "semillero del mundo", "tifón de boyacá", "criollos"],
    "Talleres de Córdoba": ["talleres", "talleres cba", "la t", "matador", "albiazul"],
    "Belgrano de Córdoba": ["belgrano", "belgrano cba", "pirata", "celeste", "la b", "los de alberdi"],
    "Colón de Santa Fe": ["colón", "colon", "sabalero", "sabalé", "rojinegro", "negro", "raza"],
    "Unión de Santa Fe": ["unión", "union", "tatengue", "el tate", "rojiblanco", "club de la avenida"],
    "Defensa y Justicia": ["defensa y justicia", "dyj", "el halcón", "halcón"],
    "Atlético Tucumán": ["atlético tucumán", "decano", "pituco", "el gigante del norte"],
    "Godoy Cruz Antonio Tomba": ["godoy cruz", "tomba", "bodeguero"],
    "Sarmiento de Junín": ["sarmiento", "sarmiento de junín", "el verde", "verdolaga", "guerrero"],
    "Platense": ["platense", "calamar", "marrón"],
    "Barracas Central": ["barracas central", "guapo"],
    "Central Córdoba (Santiago del Estero)": ["central córdoba sde", "central córdoba", "ferroviario"],
    "Instituto Atlético Central Córdoba": ["instituto", "la gloria", "albirrojo"],
    "Deportivo Riestra": ["riestra", "deportivo riestra", "malevo", "blanquinegro", "los malevos de pompeya"],
    "Independiente Rivadavia": ["independiente rivadavia", "la lepra mendocina", "azul del parque"],
    "Aldosivi": ["aldosivi", "tiburón", "el más grande de la costa atlántica", "equipo de la ciudad"],
    "San Martín (San Juan)": ["san martín sj", "san martín de san juan", "santo", "verdinegro", "la banda del pueblo viejo"],
    "San Martín (Tucumán)": ["san martín tucumán", "san martín de tucumán", "santo tucumano", "ciruja"],
    "Agropecuario Argentino": ["agropecuario", "sojero"],
    "All Boys": ["all boys", "albo"],
    "Almagro": ["almagro", "tricolor"],
    "Almirante Brown": ["almirante brown", "la fragata", "mirasol"],
    "Alvarado": ["alvarado", "torito"],
    "Arsenal Fútbol Club": ["arsenal", "el arse", "los del viaducto"],
    "Atlanta": ["atlanta", "bohemio"],
    "Chacarita Juniors": ["chacarita", "funebrero"],
    "Chaco For Ever": ["chaco for ever", "el negro"],
    "Colegiales": ["colegiales", "tricolor de munro"],
    "Defensores de Belgrano": ["defensores de belgrano", "defensores", "el dragón"],
    "Defensores Unidos": ["defensores unidos", "cadu", "celeste"],
    "Deportivo Madryn": ["deportivo madryn", "el aurinegro"],
    "Deportivo Maipú": ["deportivo maipú", "cruzado", "botellero"],
    "Deportivo Morón": ["morón", "deportivo morón", "el gallo"],
    "Estudiantes (Buenos Aires)": ["estudiantes ba", "estudiantes de caseros", "pincha de caseros", "matador"],
    "Estudiantes (Río Cuarto)": ["estudiantes río cuarto", "celeste", "león del imperio"],
    "Ferro Carril Oeste": ["ferro", "verdolaga", "oeste"],
    "Gimnasia y Esgrima (Jujuy)": ["gimnasia de jujuy", "lobo jujeño"],
    "Gimnasia y Esgrima (Mendoza)": ["gimnasia de mendoza", "lobo del parque", "mensana", "pituco"],
    "Gimnasia y Tiro (Salta)": ["gimnasia y tiro", "albo", "millonario"],
    "Los Andes": ["los andes", "milrayitas"],
    "Mitre (Santiago del Estero)": ["mitre sde", "aurinegro"],
    "Nueva Chicago": ["nueva chicago", "chicago", "torito", "torito de mataderos", "verdinegro"],
    "Patronato": ["patronato", "patrón", "rojinegro", "santo"],
    "Racing (Córdoba)": ["racing de córdoba", "la academia cordobesa", "nueva italia"],
    "San Miguel": ["san miguel", "el trueno verde"],
    "San Telmo": ["san telmo", "candombero"],
    "Talleres (Remedios de Escalada)": ["talleres re", "el tallarín", "rojiblanco"],
    "Temperley": ["temperley", "gasolero", "celeste"],
    "Tristán Suárez": ["tristán suárez", "lechero"],
    "Brown de Adrogué": ["brown de adrogué", "tricolor"],
    "Argentino de Quilmes": ["argentino de quilmes", "mate"],
    "Villa Dálmine": ["villa dálmine", "el viola", "violeta"],
    "Sportivo Italiano": ["sportivo italiano", "azzurro", "tano"],
    "Sacachispas": ["sacachispas", "lila"],
    "Flandria": ["flandria", "canario"],
    "Comunicaciones": ["comunicaciones", "cartero"],
    "Cipolletti": ["cipolletti", "albinegro", "capataz de la patagonia"],
    "Olimpo": ["olimpo", "aurinegro"],
    "Juventud Antoniana": ["juventud antoniana", "santo salteño"],
    "Villa Mitre (Bahía Blanca)": ["villa mitre", "tricolor", "villero"],
    "Argentino de Rosario": ["argentino de rosario", "salaíto"],
    "Berazategui": ["berazategui", "naranja", "el bera"],
    "Central Córdoba (Rosario)": ["central córdoba rosario", "charrúa"],
    "Claypole": ["claypole", "tambero"],
    "Deportivo Español": ["deportivo español", "gallego"],
    "Ituzaingó": ["ituzaingó", "león verde", "el verde"],
    "Luján": ["luján", "lujanero"]
}

# Diccionario que será utilizado en la detección - puede ser el completo o filtrado según el contexto
EQUIPOS_MVP = {}

# --- Carga de Diccionario de Jugadores MVP ---
JUGADORES_MVP = {}  # Este diccionario se llenará con los datos cargados de los archivos JSON

def load_players_dictionary(home_team=None, away_team=None):
    """
    Carga los diccionarios de jugadores. Si se especifican home_team y away_team,
    solo carga los jugadores de esos equipos específicos.
    
    Args:
        home_team (str, optional): Nombre canónico del equipo local
        away_team (str, optional): Nombre canónico del equipo visitante
    """
    global JUGADORES_MVP, EQUIPOS_MVP
    players_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                               'data', 'dictionaries', 'team_players')
    
    # Filtrar EQUIPOS_MVP si estamos en un contexto de partido específico
    if MATCH_CONTEXT_ENABLED and home_team and away_team:
        logging.info(f"Cargando contexto específico para el partido: {home_team} vs {away_team}")
        # Filtrar EQUIPOS_MVP para incluir solo los equipos del partido
        EQUIPOS_MVP_FILTRADO = {k: v for k, v in EQUIPOS_MVP_COMPLETO.items() 
                              if k == home_team or k == away_team}
        EQUIPOS_MVP = EQUIPOS_MVP_FILTRADO
        
        # Preparar para cargar solo archivos de los equipos relevantes
        home_team_file = convert_team_name_to_filename(home_team)
        away_team_file = convert_team_name_to_filename(away_team)
        
        json_files = [
            os.path.join(players_dir, home_team_file),
            os.path.join(players_dir, away_team_file)
        ]
        
        logging.info(f"Buscando archivos de jugadores para: {home_team_file}, {away_team_file}")
    else:
        logging.info("Cargando todos los equipos y jugadores (sin contexto específico de partido)")
        EQUIPOS_MVP = EQUIPOS_MVP_COMPLETO
        json_files = glob.glob(os.path.join(players_dir, '*.json'))
    
    if not json_files:
        logging.warning(f"No se encontraron archivos de diccionario de jugadores en {players_dir}")
        return
    
    # Cargar archivos JSON
    for json_file in json_files:
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    team_players = json.load(f)
                    JUGADORES_MVP.update(team_players)
                logging.info(f"Cargado diccionario de jugadores desde {os.path.basename(json_file)}")
            else:
                logging.warning(f"Archivo de equipo no encontrado: {json_file}")
        except Exception as e:
            logging.error(f"Error al cargar diccionario de jugadores desde {json_file}: {e}")
    
    if MATCH_CONTEXT_ENABLED and home_team and away_team:
        logging.info(f"Cargados {len(JUGADORES_MVP)} jugadores para el partido {home_team} vs {away_team}.")
    else:
        logging.info(f"Cargados {len(JUGADORES_MVP)} jugadores en total.")

def convert_team_name_to_filename(team_name):
    """
    Convierte un nombre canónico de equipo al formato esperado para el nombre de archivo.
    Ejemplo: "River Plate" -> "river_plate.json"
    
    Args:
        team_name (str): Nombre canónico del equipo
        
    Returns:
        str: Nombre de archivo esperado
    """
    if not team_name:
        return ""
        
    return team_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', '') + '.json'

# Cargar los diccionarios de jugadores al inicio
try:
    load_players_dictionary(MATCH_HOME_TEAM, MATCH_AWAY_TEAM)
except Exception as e:
    logging.error(f"Error al cargar diccionarios de jugadores: {e}", exc_info=True)
    # Continuamos con un diccionario vacío si hay un error en la carga

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
    text = re.sub(r'\\s+', ' ', text).strip() # Reemplazar múltiples espacios con uno solo y quitar espacios al inicio/final
    # Aquí se podrían añadir más reglas de limpieza (ej. remover emojis, URLs, etc.)
    return text

def analyze_sentiment_mvp(text_to_analyze):
    """
    Analiza el sentimiento de un texto usando diccionarios de palabras clave y manejo básico de negaciones.
    Prioriza frases más largas sobre palabras individuales.
    """
    try:
        if not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
            logging.info("Análisis de sentimiento: texto vacío o no válido, retornando neutral")
            return {"label": "neutral", "score": 0.0}

        text_lower = text_to_analyze.lower() # Normalizar a minúsculas una vez
        total_score = 0.0
        
        # Registrar información de depuración para ver la longitud del texto
        logging.info(f"Analizando sentimiento para texto de {len(text_lower)} caracteres")
        
        # Pre-procesar diccionarios para tener una lista única de tuplas (frase, score)
        sentiment_terms = []
        for term, score in DICCIONARIO_POSITIVAS_MVP.items():
            sentiment_terms.append((term.lower(), score))
        for term, score in DICCIONARIO_NEGATIVAS_MVP.items():
            sentiment_terms.append((term.lower(), score))
        
        # Ordenar por longitud de la frase (clave[0]) de forma descendente
        sentiment_terms.sort(key=lambda x: len(x[0]), reverse=True)
        logging.debug(f"Preparados {len(sentiment_terms)} términos para análisis de sentimiento")

        # Para el manejo de negaciones, dividimos el texto en "palabras" para chequear la anterior.
        words_for_negation_check = text_lower.split()
        
        processed_text = text_lower # Hacemos una copia para ir "consumiendo" las partes procesadas
        
        # Limitar el número máximo de términos para prevenir bucles extremadamente largos
        max_iterations = 1000
        iteration_count = 0
        
        for term, score in sentiment_terms:
            # Verificar si hemos excedido el límite de iteraciones para prevenir bucles infinitos
            iteration_count += 1
            if iteration_count > max_iterations:
                logging.warning(f"Se alcanzó el límite de {max_iterations} iteraciones en análisis de sentimiento")
                break
                
            term_len = len(term)
            # Buscar todas las ocurrencias no solapadas del término
            start_index = 0
            # Establecer un límite para el bucle interno también
            max_inner_iterations = 100
            inner_iteration = 0
            
            while start_index < len(processed_text) and inner_iteration < max_inner_iterations:
                inner_iteration += 1
                found_pos = processed_text.find(term, start_index)
                if found_pos == -1: # No más ocurrencias de este término
                    break

                # Verificar negación (simplificado para MVP)
                negation_multiplier = 1.0
                
                # Hacer más robusto el cálculo del inicio de la ventana
                preceding_text_window_start = max(0, found_pos - min(50, found_pos))  # Usar una ventana fija máxima
                preceding_text_for_negation = text_lower[preceding_text_window_start:found_pos]
                
                # Dividir esta ventana en palabras y chequear las últimas
                potential_negators = preceding_text_for_negation.split()
                if len(potential_negators) > 0:
                    # Verificar solo las últimas 3 palabras para evitar problemas con textos muy largos
                    words_to_check_for_negation = potential_negators[-3:] 
                    for neg_word in PALABRAS_NEGACION_MVP:
                        if neg_word in words_to_check_for_negation:
                            negation_multiplier = -1.0
                            break
            
                total_score += score * negation_multiplier
                
                # "Consumir" el término encontrado para evitar re-procesarlo
                try:
                    processed_text = processed_text[:found_pos] + (' ' * term_len) + processed_text[found_pos + term_len:]
                    start_index = found_pos + term_len
                except Exception as e:
                    logging.error(f"Error al procesar texto en posición {found_pos}: {e}")
                    # En caso de error, avanzar para evitar bucle infinito
                    start_index = len(processed_text)

            # Si el bucle interno alcanzó su límite, registrarlo
            if inner_iteration >= max_inner_iterations:
                logging.warning(f"Bucle interno alcanzó límite de {max_inner_iterations} para el término '{term}'")

        # Determinar etiqueta basada en el score total
        if total_score > 0.15:
            label = "positive"
        elif total_score < -0.15:
            label = "negative"
        else:
            label = "neutral"
            
        logging.info(f"Análisis completado con éxito. Score: {total_score}, Label: {label}")
        return {"label": label, "score": round(total_score, 2)}
        
    except Exception as e:
        logging.error(f"Error en análisis de sentimiento: {e}", exc_info=True)
        # En caso de error, devolver un valor por defecto
        return {"label": "neutral", "score": 0.0, "error": str(e)}

def detect_mentioned_teams_mvp(text_to_analyze, equipos_dict):
    """
    Detecta equipos mencionados en un texto usando un diccionario de equipos y sus alias.
    Devuelve una lista de nombres canónicos de equipos encontrados.
    La búsqueda de alias es case-insensitive y busca coincidencias como palabras completas.
    
    Si se ha activado el contexto específico de partido, dará prioridad a los equipos
    del partido actual.
    """
    try:
        if not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
            logging.info("detect_mentioned_teams_mvp: texto vacío o no válido, retornando lista vacía")
            return []
        if not equipos_dict:
            logging.warning("detect_mentioned_teams_mvp: diccionario de equipos vacío, retornando lista vacía")
            return []

        logging.info(f"Buscando equipos mencionados en texto de {len(text_to_analyze)} caracteres")
        text_lower = text_to_analyze.lower()
        found_teams_canonical_names = set()

        # Chequeo especial para equipos del contexto si está activado
        if MATCH_CONTEXT_ENABLED and MATCH_HOME_TEAM and MATCH_AWAY_TEAM:
            logging.debug(f"Contexto de partido activado: {MATCH_HOME_TEAM} vs {MATCH_AWAY_TEAM}")
            priority_teams = [MATCH_HOME_TEAM, MATCH_AWAY_TEAM]
            for team_name in priority_teams:
                if team_name in equipos_dict:
                    for alias in equipos_dict[team_name]:
                        try:
                            alias_lower = alias.lower()
                            pattern = r'\b' + re.escape(alias_lower) + r'\b'
                            if re.search(pattern, text_lower):
                                found_teams_canonical_names.add(team_name)
                                logging.debug(f"Encontrado equipo prioritario: {team_name} (alias: {alias_lower})")
                                break
                        except re.error as e:
                            logging.warning(f"Error de regex para alias '{alias_lower}' del equipo '{team_name}': {e}")
                            continue
                        except Exception as e:
                            logging.error(f"Error inesperado al buscar alias '{alias}' del equipo '{team_name}': {e}")
                            continue
            
            # Si ya encontramos equipos en el contexto, retornamos inmediatamente
            if found_teams_canonical_names:
                logging.info(f"Equipos encontrados en contexto prioritario: {', '.join(found_teams_canonical_names)}")
                # Transformar los nombres canónicos en la estructura de diccionario esperada
                result = []
                for team_canonical_name in found_teams_canonical_names:
                    result.append({"name": team_canonical_name})
                return result
        
        # Procesamiento normal para todos los equipos (o si no se encontraron equipos del contexto)
        # Limitar el número de equipos a verificar para prevenir problemas de rendimiento
        max_teams = 50  # Limitar a un número razonable en caso de diccionarios muy grandes
        team_count = 0
        
        for canonical_name, aliases in equipos_dict.items():
            team_count += 1
            if team_count > max_teams:
                logging.warning(f"Se alcanzó el límite de {max_teams} equipos verificados")
                break
                
            # Limitar el número de alias por equipo también
            max_aliases = 30
            alias_count = 0
            
            for alias in aliases:
                alias_count += 1
                if alias_count > max_aliases:
                    logging.debug(f"Se omitieron algunos alias para {canonical_name} (límite: {max_aliases})")
                    break
                    
                try:
                    alias_lower = alias.lower()
                    pattern = r'\b' + re.escape(alias_lower) + r'\b'
                    if re.search(pattern, text_lower):
                        found_teams_canonical_names.add(canonical_name)
                        logging.debug(f"Encontrado equipo: {canonical_name} (alias: {alias_lower})")
                        break
                except re.error as e:
                    logging.warning(f"Error de regex para alias '{alias_lower}' del equipo '{canonical_name}': {e}")
                    continue
                except Exception as e:
                    logging.error(f"Error inesperado al buscar alias '{alias}' del equipo '{canonical_name}': {e}")
                    continue
                    
        # Transformar los nombres canónicos en la estructura de diccionario esperada
        result = []
        for team_canonical_name in found_teams_canonical_names:
            result.append({"name": team_canonical_name})
            
        if result:
            logging.info(f"Total equipos encontrados: {len(result)}")
        else:
            logging.info("No se encontraron equipos mencionados")
            
        return result
        
    except Exception as e:
        logging.error(f"Error general en detect_mentioned_teams_mvp: {e}", exc_info=True)
        return []  # En caso de error, devolver una lista vacía

def detect_mentioned_players_mvp(text_to_analyze):
    """
    Detecta jugadores mencionados en un texto usando el diccionario JUGADORES_MVP.
    Devuelve una lista de objetos con nombre canónico del jugador y su equipo actual.
    La búsqueda de alias es case-insensitive y busca coincidencias como palabras completas.
    
    Si se ha activado el contexto específico de partido, solo considerará jugadores
    de los equipos participantes, evitando falsos positivos.
    """
    try:
        if not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
            logging.info("detect_mentioned_players_mvp: texto vacío o no válido, retornando lista vacía")
            return []
        if not JUGADORES_MVP:
            logging.warning("Diccionario JUGADORES_MVP vacío. No es posible la detección de jugadores.")
            return []

        logging.info(f"Buscando jugadores mencionados en texto de {len(text_to_analyze)} caracteres")
        text_lower = text_to_analyze.lower()
        found_players = []

        # Verificamos primero si se menciona algún equipo - útil para desambiguación
        # Para evitar una recursión potencialmente problemática, vamos a extraer los equipos mencionados directamente
        mentioned_teams = []
        mentioned_team_names = []
        
        try:
            # Usamos detect_mentioned_teams_mvp pero con manejo de errores específico
            mentioned_teams = detect_mentioned_teams_mvp(text_lower, EQUIPOS_MVP)
            mentioned_team_names = [team["name"] for team in mentioned_teams] if mentioned_teams else []
            logging.debug(f"Equipos mencionados para detección de jugadores: {', '.join(mentioned_team_names) if mentioned_team_names else 'ninguno'}")
        except Exception as e:
            logging.error(f"Error al detectar equipos para contexto de jugadores: {e}")
            # Continuamos con lista vacía en caso de error

        # Limitar el número máximo de jugadores a verificar
        max_players = 100  # Limitar a un número razonable en caso de diccionarios muy grandes
        player_count = 0
        
        for canonical_name, player_info in JUGADORES_MVP.items():
            player_count += 1
            if player_count > max_players:
                logging.warning(f"Se alcanzó el límite de {max_players} jugadores verificados")
                break
                
            try:
                aliases = player_info.get('aliases', [])
                equipo_actual = player_info.get('equipo_actual', '')
                
                # Si estamos en contexto de partido y hay equipos mencionados,
                # verificamos si este jugador pertenece a alguno de ellos para priorizar
                if MATCH_CONTEXT_ENABLED and mentioned_team_names:
                    # Si el jugador no pertenece a ningún equipo mencionado en el texto,
                    # y tampoco a los equipos del partido, le damos menor prioridad
                    player_team_mentioned = equipo_actual in mentioned_team_names
                    player_in_match_teams = equipo_actual in [MATCH_HOME_TEAM, MATCH_AWAY_TEAM]
                    
                    if not (player_team_mentioned or player_in_match_teams):
                        continue  # Omitir jugadores que no están en el contexto relevante
                
                # Limitar el número de alias por jugador
                max_aliases = 20
                alias_count = 0
                
                for alias in aliases:
                    alias_count += 1
                    if alias_count > max_aliases:
                        logging.debug(f"Se omitieron algunos alias para {canonical_name} (límite: {max_aliases})")
                        break
                        
                    try:
                        alias_lower = alias.lower()
                        pattern = r'\b' + re.escape(alias_lower) + r'\b'
                        if re.search(pattern, text_lower):
                            # Añadir jugador con su información si no está ya en la lista
                            player_obj = {
                                "name": canonical_name,
                                "team": equipo_actual
                            }
                            if player_obj not in found_players:  # Evitar duplicados
                                found_players.append(player_obj)
                                logging.debug(f"Encontrado jugador: {canonical_name} (alias: {alias_lower})")
                            break  # Si ya encontramos un alias para este jugador, pasamos al siguiente
                    except re.error as e:
                        logging.warning(f"Error de regex para alias '{alias_lower}' del jugador '{canonical_name}': {e}")
                        continue
                    except Exception as e:
                        logging.error(f"Error inesperado al buscar alias '{alias}' del jugador '{canonical_name}': {e}")
                        continue
            except Exception as e:
                logging.error(f"Error procesando jugador {canonical_name}: {e}")
                continue
        
        # Desambiguación: si tenemos jugadores de diferentes equipos y algunos son del contexto del partido,
        # y otros no, priorizamos los del partido
        if MATCH_CONTEXT_ENABLED and found_players and len(found_players) > 1:
            try:
                match_team_players = [p for p in found_players if p.get('team') in [MATCH_HOME_TEAM, MATCH_AWAY_TEAM]]
                if match_team_players:
                    logging.info(f"Aplicando desambiguación: {len(match_team_players)} jugadores del partido de {len(found_players)} detectados")
                    return match_team_players
            except Exception as e:
                logging.error(f"Error durante desambiguación de jugadores: {e}")
                # Continuamos con todos los jugadores en caso de error
        
        if found_players:
            logging.info(f"Total jugadores encontrados: {len(found_players)}")
        else:
            logging.info("No se encontraron jugadores mencionados")
            
        return found_players
        
    except Exception as e:
        logging.error(f"Error general en detect_mentioned_players_mvp: {e}", exc_info=True)
        return []  # En caso de error, devolver una lista vacía

def process_message(message_id, message_data):
    """Procesa un único mensaje del stream: deserializa, valida y enriquece."""
    try:
        msg_id_str = message_id.decode() if isinstance(message_id, bytes) else message_id
        logging.info(f"🔄 INICIANDO PROCESAMIENTO DEL MENSAJE: {msg_id_str}")
        
        # El payload del mensaje es una cadena JSON
        comment_payload_str = message_data.get('payload')
        if not comment_payload_str:
            logging.warning(f"❌ Mensaje {msg_id_str} no tiene campo 'payload'. Omitiendo.")
            return None

        # Log para depuración
        logging.info(f"📦 PAYLOAD RECIBIDO: {comment_payload_str[:100]}...")
        
        # Paso 1: Decodificar JSON
        comment_dict = {}
        try:
            comment_dict = json.loads(comment_payload_str)
        except json.JSONDecodeError as e:
            logging.error(f"❌ Error al decodificar JSON para mensaje {msg_id_str}: {e}. Payload: {comment_payload_str[:200]}... Omitiendo.")
            return None
        
        # Paso 2: Validar campos esperados
        missing_fields = [field for field in EXPECTED_FIELDS if field not in comment_dict]
        if missing_fields:
            logging.warning(f"⚠️ Mensaje {msg_id_str} (source_comment_id: {comment_dict.get('source_comment_id', 'N/A')}) le faltan campos: {missing_fields}. Omitiendo.")
            return None

        # Paso 3: Mostrar el texto original para depuración
        original_text = comment_dict.get("original_text", "")
        logging.info(f"📝 TEXTO ORIGINAL: '{original_text}'")

        # Paso 4: Enriquecimiento básico
        try:
            comment_dict["internal_comment_id"] = str(uuid.uuid4())
            comment_dict["processing_timestamp_utc"] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            comment_dict["cleaned_text"] = clean_text(comment_dict.get("original_text", ""))
            
            if not comment_dict["cleaned_text"]:
                logging.warning(f"⚠️ Mensaje {msg_id_str} tiene texto limpio vacío después de procesamiento.")
                # Continuamos con texto vacío, pero advertimos
        except Exception as e:
            logging.error(f"❌ Error en enriquecimiento básico: {e}", exc_info=True)
            # Si falla este paso, podríamos aún procesar con valores por defecto
            if "cleaned_text" not in comment_dict:
                comment_dict["cleaned_text"] = ""
        
        # Paso 5: Análisis de Sentimiento MVP - con manejo de errores
        try:
            if comment_dict.get("cleaned_text"): # Solo analizar si hay texto limpio
                logging.info(f"🧹 TEXTO LIMPIO: '{comment_dict['cleaned_text']}'")
                sentiment_result = analyze_sentiment_mvp(comment_dict["cleaned_text"])
                comment_dict["sentiment_analysis"] = sentiment_result
                logging.info(f"😀 SENTIMIENTO: {sentiment_result['label']} (score: {sentiment_result['score']})")
            else:
                comment_dict["sentiment_analysis"] = {"label": "neutral", "score": 0.0} # Default si no hay texto
                logging.info("⚠️ SIN TEXTO PARA ANALIZAR SENTIMIENTO - usando neutral")
        except Exception as e:
            logging.error(f"❌ Error en análisis de sentimiento: {e}", exc_info=True)
            comment_dict["sentiment_analysis"] = {"label": "neutral", "score": 0.0, "error": str(e)}
        # --- Fin Análisis de Sentimiento ---

        # Paso 6: Detección de Equipos MVP
        try:
            if comment_dict.get("cleaned_text"):
                mentioned_teams = detect_mentioned_teams_mvp(comment_dict["cleaned_text"], EQUIPOS_MVP)
                comment_dict["mentioned_teams"] = mentioned_teams
                if mentioned_teams:
                    logging.info(f"⚽ EQUIPOS MENCIONADOS: {', '.join([team['name'] for team in mentioned_teams])}")
                else:
                    logging.info("⚽ NO SE DETECTARON EQUIPOS")
            else:
                comment_dict["mentioned_teams"] = [] # Default si no hay texto
        except Exception as e:
            logging.error(f"❌ Error en detección de equipos: {e}", exc_info=True)
            comment_dict["mentioned_teams"] = []
        # --- Fin Detección de Equipos ---

        # Paso 7: Detección de Jugadores MVP
        try:
            if comment_dict.get("cleaned_text"):
                mentioned_players = detect_mentioned_players_mvp(comment_dict["cleaned_text"])
                comment_dict["mentioned_players"] = mentioned_players
                if mentioned_players:
                    logging.info(f"👤 JUGADORES MENCIONADOS: {', '.join([player['name'] for player in mentioned_players])}")
                else:
                    logging.info("👤 NO SE DETECTARON JUGADORES")
            else:
                comment_dict["mentioned_players"] = [] # Default si no hay texto
        except Exception as e:
            logging.error(f"❌ Error en detección de jugadores: {e}", exc_info=True)
            comment_dict["mentioned_players"] = []
        # --- Fin Detección de Jugadores ---

        # Paso 8: Información del Contexto (si está habilitado)
        try:
            if MATCH_CONTEXT_ENABLED and MATCH_HOME_TEAM and MATCH_AWAY_TEAM:
                comment_dict["match_context"] = {
                    "home_team": MATCH_HOME_TEAM,
                    "away_team": MATCH_AWAY_TEAM
                }
        except Exception as e:
            logging.error(f"❌ Error al agregar contexto de partido: {e}")
            # No es crítico, el procesamiento puede continuar sin contexto
        # --- Fin Información del Contexto ---

        logging.info(f"✅ Mensaje {msg_id_str} procesado exitosamente (internal_id: {comment_dict['internal_comment_id']})")
        return comment_dict

    except json.JSONDecodeError as e:
        logging.error(f"❌ Error al decodificar JSON para mensaje {message_id}: {e}. Payload: {comment_payload_str[:200] if 'comment_payload_str' in locals() else 'N/A'}... Omitiendo.")
        return None
    except Exception as e:
        logging.error(f"❌ Error inesperado al procesar mensaje {message_id}: {e}", exc_info=True)
        return None

def consume_and_process_comments(redis_client, stream_name, group_name, consumer_name):
    """Bucle principal para consumir y procesar comentarios del stream de Redis."""
    logging.info(f"✨ INICIANDO CONSUMIDOR '{consumer_name}' para grupo '{group_name}' en stream '{stream_name}'.")
    logging.info(f"⏳ Esperando mensajes...")
    
    # Variables para seguimiento
    total_messages_processed = 0
    total_messages_failed = 0
    batch_number = 0

    while True:
        try:
            batch_number += 1
            # Leer mensajes del stream para este consumidor y grupo
            # '>' significa leer mensajes nuevos que no han sido entregados a otros consumidores del grupo
            logging.info(f"👂 Escuchando nuevos mensajes en stream '{stream_name}' (lote #{batch_number})...")
            messages = redis_client.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: '>'}, # El '>' es para mensajes nuevos
                count=READ_COUNT,
                block=BLOCK_MILLISECONDS
            )

            if not messages:
                # No hay mensajes nuevos después del tiempo de bloqueo, el bucle continúa y reintenta
                logging.info(f"😴 No se recibieron mensajes nuevos después de {BLOCK_MILLISECONDS/1000:.1f} segundos, continuando escucha...")
                continue

            # messages es una lista de tuplas: [(stream_name, [(message_id, message_data_dict)])]
            for stream, message_list in messages:
                stream_name_str = stream.decode() if isinstance(stream, bytes) else stream
                logging.info(f"📨 Recibidos {len(message_list)} mensajes del stream '{stream_name_str}'")
                
                message_ids_to_ack = []
                for message_id, message_data in message_list:
                    msg_id_str = message_id.decode() if isinstance(message_id, bytes) else message_id
                    logging.info(f"📩 Procesando mensaje {msg_id_str} (Total hasta ahora: {total_messages_processed + len(message_ids_to_ack) + 1})")
                    
                    # Imprimir datos brutos del mensaje para diagnóstico
                    logging.debug(f"DATOS DEL MENSAJE {msg_id_str}: {message_data}")
                    
                    try:
                        # Procesamos el mensaje con un tiempo límite implícito (sin bloquear el loop principal)
                        enriched_comment = process_message(message_id, message_data)

                        if enriched_comment:
                            # Por ahora, solo imprimir el comentario enriquecido
                            enriched_json = json.dumps(enriched_comment, indent=2, ensure_ascii=False)
                            print("\n" + "="*80)
                            print(f"COMENTARIO PROCESADO #{total_messages_processed + 1}:")
                            print("="*80)
                            print(enriched_json)
                            print("="*80 + "\n")
                            
                            message_ids_to_ack.append(message_id)
                            total_messages_processed += 1
                            logging.info(f"✅ Mensaje {msg_id_str} procesado correctamente. Total exitosos: {total_messages_processed}")
                        else:
                            # El mensaje no pudo ser procesado, pero aún así hacemos ACK
                            # Para evitar que quede pendiente indefinidamente
                            if message_data.get('payload'): # Solo si hubo payload para intentar procesar
                                message_ids_to_ack.append(message_id)
                                logging.warning(f"⚠️ Mensaje {msg_id_str} no pudo ser procesado pero se reconoce (ACK)")
                                total_messages_failed += 1
                    except Exception as e:
                        logging.error(f"❌ Error inesperado procesando mensaje {msg_id_str}: {e}", exc_info=True)
                        # Aún con error, hacemos ACK para evitar que quede pendiente
                        message_ids_to_ack.append(message_id)
                        total_messages_failed += 1

                # Intentar hacer ACK de todos los mensajes procesados o con error
                if message_ids_to_ack:
                    try:
                        # Acusar recibo de los mensajes procesados (o conscientemente omitidos)
                        ack_result = redis_client.xack(stream_name, group_name, *message_ids_to_ack)
                        logging.info(f"✅ ACK para {ack_result} mensajes. Resumen lote #{batch_number}: {len(message_ids_to_ack)} procesados, {total_messages_processed} exitosos total, {total_messages_failed} fallidos total.")
                    except Exception as e:
                        logging.error(f"❌ Error al hacer ACK de mensajes: {e}", exc_info=True)
                        # Aquí podríamos implementar un reintento del ACK, pero por ahora solo registramos el error

        except redis.exceptions.RedisError as e:
            logging.error(f"❌ Error de Redis durante el bucle de consumo: {e}. Intentando reconectar en 5s...")
            time.sleep(5)
            # Podríamos intentar reconectar aquí, pero por simplicidad, si la conexión se pierde de forma crítica,
            # el script podría necesitar reiniciarse. La librería redis-py maneja algunas reconexiones.
        except KeyboardInterrupt:
            logging.info(f"🛑 Proceso interrumpido por el usuario. Total procesados: {total_messages_processed}, Fallidos: {total_messages_failed}. Saliendo...")
            break
        except Exception as e:
            logging.error(f"❌ Error inesperado en el bucle principal: {e}", exc_info=True)
            # Esperar un poco antes de reintentar para evitar un bucle apretado en caso de errores persistentes
            time.sleep(5)

if __name__ == "__main__":
    # Imprimir información del contexto del partido al inicio
    if MATCH_CONTEXT_ENABLED and MATCH_HOME_TEAM and MATCH_AWAY_TEAM:
        logging.info(f"Procesador iniciado en modo CONTEXTO DE PARTIDO: {MATCH_HOME_TEAM} vs {MATCH_AWAY_TEAM}")
        logging.info(f"Equipos cargados: {len(EQUIPOS_MVP)}, Jugadores cargados: {len(JUGADORES_MVP)}")
    else:
        logging.info("Procesador iniciado en modo GENERAL (sin contexto específico de partido)")
        logging.info(f"Equipos cargados: {len(EQUIPOS_MVP)}, Jugadores cargados: {len(JUGADORES_MVP)}")
    
    redis_conn = connect_to_redis(REDIS_HOST, REDIS_PORT)

    if redis_conn:
        try:
            create_consumer_group_if_not_exists(redis_conn, REDIS_STREAM_NAME, REDIS_CONSUMER_GROUP_NAME)
            consume_and_process_comments(redis_conn, REDIS_STREAM_NAME, REDIS_CONSUMER_GROUP_NAME, REDIS_CONSUMER_NAME)
        except Exception as e:
            logging.critical(f"Failed to initialize or run consumer: {e}", exc_info=True)
    else:
        logging.critical("Could not connect to Redis. Exiting processor.") 