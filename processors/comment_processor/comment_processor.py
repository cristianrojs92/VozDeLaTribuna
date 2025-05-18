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
    "bancan": 1.2, "🤑": 1.0, "sacalaaa": 0.9
}

DICCIONARIO_NEGATIVAS_MVP = {
    # Decepción, Enojo, Crítica General
    "desastre": -1.5, "horrible": -1.4, "mal": -0.8, "malo": -1.0, "malos": -1.0,
    "malísimo": -1.3, "malisimo": -1.3, "pésimo": -1.4, "pesimo": -1.4, "decepcion": -1.2,
    "decepción": -1.2, "frustrante": -1.1, "que mal": -1.0, "qué mal": -1.0,
    "mamita querida": -0.9, "no puede ser": -0.8, "asi no": -0.9, "así no": -0.9,
    "para el olvido": -1.2, "verguenza": -1.5, "vergüenza": -1.5, "lamentable": -1.3,
    "desilusion": -1.1, "desilusión": -1.1, "bronca": -1.0, "caliente": -0.9, "calentura": -1.0,
    # Insultos/Críticas a Jugadores/Equipo
    "burro": -1.3, "muerto": -1.6, "muertos": -1.6, "perro": -1.4, "tronco": -1.5,
    "paquete": -1.5, "pecho frio": -1.8, "pechofrío": -1.8, "pechos frios": -1.8,
    "pechosfríos": -1.8, "patadura": -1.2, "equipo chico": -1.0, "no juegan a nada": -1.4,
    "son un desastre": -1.3, "morfón": -1.6, "morfon": -1.6, "cagon": -1.7, "cagón": -1.7,
    "vendehumo": -1.5, "chambon": -1.2, "chambón": -1.2, "fantasma": -1.1, "impresentable": -1.4,
    "desaparecido": -1.0, "horribles": -1.4, "asco": -1.6, "dan asco": -1.7,
    "muerto de hambre": -1.5,
    # Insultos Fuertes / Agresión (comunes en chat)
    "la concha de tu madre": -2.0, "lcdtm": -2.0, "hijo de puta": -1.9, "hdp": -1.9,
    "forro": -1.7, "pelotudo": -1.6, "boludo": -1.0, "andate a la mierda": -1.8,
    "puto": -1.8, "orto": -1.5, "culo roto": -1.7,
    # Críticas al Arbitraje / Juego Sucio
    "robo": -1.7, "afano": -1.7, "ladron": -1.6, "ladrón": -1.6, "chorro": -1.6,
    "comprado": -1.5, "penalazo no cobrado": -1.3, "era roja": -1.1, "cobra bien": -0.5,
    "referi horrible": -1.4, "árbitro horrible": -1.4, "mal arbitraje": -1.3,
    "nos robaron": -1.7, "nos cagaron": -1.7, "cagaron": -1.7,
    # Mal Rendimiento
    "mal rendimiento": -1.0, "no corren": -1.2, "se arrastran": -1.3, "erro solo": -1.1,
    "erró solo": -1.1, "se comio un gol": -1.3, "se comió un gol": -1.3,
    "colgarse del travesaño": -0.8, "cascotear el rancho": -0.5, "cerrarse el arco": -0.7,
    "no patean al arco": -1.1, "sin ideas": -1.0, "falta actitud": -1.2, "baja el nivel": -0.9,
    # Emojis Negativos
    "👎": -1.0, "😠": -1.2, "🤦": -0.9, "💩": -1.5, "😤": -1.1, "😡": -1.3, "🥶": -1.0,
    "��": -0.8, "🙄": -0.7,
    # Nuevas adiciones basadas en análisis de comentarios
    "malisimo lcdtm": -2.2, "ni ganas": -0.9, "humo": -1.3, "un kilo": -1.4,
    "afk": -0.8, "bodrio": -1.2, "😐": -0.4, "😑": -0.4
}

PALABRAS_NEGACION_MVP = [
    "no", "ni", "nunca", "jamas", "jamás", "tampoco", "sin", "nadie"
]

# --- Diccionario para Detección de Equipos MVP ---
EQUIPOS_MVP = {
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
    if not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
        return {"label": "neutral", "score": 0.0}

    text_lower = text_to_analyze.lower() # Normalizar a minúsculas una vez
    total_score = 0.0
    
    # Combinar diccionarios y ordenar por longitud de clave (descendente) para priorizar frases
    # Esto es crucial para que "no puede ser" se detecte antes que "no" o "puede" o "ser" individualmente.
    # Los emojis suelen ser de longitud 1, por lo que se procesarán después de frases más largas.
    
    # Pre-procesar diccionarios para tener una lista única de tuplas (frase, score)
    # y ordenarla por longitud de la frase, de más larga a más corta.
    # Esto asegura que "no puede ser" se revise antes que "puede ser" o "no".
    
    sentiment_terms = []
    for term, score in DICCIONARIO_POSITIVAS_MVP.items():
        sentiment_terms.append((term.lower(), score))
    for term, score in DICCIONARIO_NEGATIVAS_MVP.items():
        sentiment_terms.append((term.lower(), score))
    
    # Ordenar por longitud de la frase (clave[0]) de forma descendente
    sentiment_terms.sort(key=lambda x: len(x[0]), reverse=True)

    # Para el manejo de negaciones, dividimos el texto en "palabras" para chequear la anterior.
    # Una tokenización simple es suficiente para este propósito en el MVP.
    # Es importante notar que la búsqueda de frases se hace sobre `text_lower` completo.
    # La tokenización aquí es solo para el contexto de negación.
    words_for_negation_check = text_lower.split()
    
    # Iterar sobre el texto buscando los términos del diccionario
    # Para evitar contar múltiples veces la misma sección de texto si hay solapamientos
    # y para manejar correctamente la negación, este bucle es más complejo.
    # Enfoque MVP simplificado: buscar cada término y si se encuentra, añadir su score.
    # Este enfoque no maneja bien solapamientos complejos ni negaciones de frases largas perfectamente,
    # pero es un punto de partida para el MVP.

    processed_text = text_lower # Hacemos una copia para ir "consumiendo" las partes procesadas
    
    for term, score in sentiment_terms:
        term_len = len(term)
        # Buscar todas las ocurrencias no solapadas del término
        start_index = 0
        while start_index < len(processed_text):
            found_pos = processed_text.find(term, start_index)
            if found_pos == -1: # No más ocurrencias de este término
                break

            # Verificar negación (simplificado para MVP)
            # Buscar la palabra que precede inmediatamente al término encontrado.
            # Esto es una aproximación. Una negación puede estar más lejos o ser más compleja.
            negation_multiplier = 1.0
            # Encontrar la "palabra" que precede a `found_pos` en el texto original tokenizado
            # Esto es heurístico y puede no ser perfecto.
            # Ejemplo: "yo no creo que sea muy bueno". "bueno" está negado por "no".
            # Si el término es una frase, como "muy bueno", necesitamos ser más cuidadosos.
            
            # Heurística simple para negación: buscar una palabra de negación en una ventana pequeña antes del término.
            # Considerar las 2 palabras antes del inicio del término encontrado.
            # Se busca en `text_lower` original, no en `processed_text` que se modifica.
            preceding_text_window_start = max(0, found_pos - (max(len(w) for w in PALABRAS_NEGACION_MVP) + len(term) + 5)) # Ventana antes
            preceding_text_for_negation = text_lower[preceding_text_window_start:found_pos]
            
            # Dividir esta ventana en palabras y chequear las últimas (ej. 2 palabras)
            potential_negators = preceding_text_for_negation.split()
            if len(potential_negators) > 0:
                # Chequear la última o las dos últimas palabras en la ventana
                words_to_check_for_negation = potential_negators[-2:] # Tomar las últimas dos palabras
                for neg_word in PALABRAS_NEGACION_MVP:
                    if neg_word in words_to_check_for_negation:
                        # Si encontramos una palabra de negación cerca y antes del término.
                        # Cuidado: esto podría negar incorrectamente si hay estructuras complejas.
                        # ej: "no es malo, es bueno". "bueno" no debería ser negado aquí por el "no" anterior.
                        # Para el MVP, asumimos una negación simple si está cerca y antes.
                        negation_multiplier = -1.0
                        break # Encontramos una negación, no necesitamos seguir buscando en esta ventana.
            
            total_score += score * negation_multiplier
            
            # "Consumir" el término encontrado para evitar re-procesarlo con términos más cortos o solapados.
            # Reemplazamos el término con espacios para mantener longitudes y posiciones relativas
            # para futuros `find` en esta iteración, aunque es una simplificación.
            processed_text = processed_text[:found_pos] + (' ' * term_len) + processed_text[found_pos + term_len:]
            start_index = found_pos + term_len # Continuar la búsqueda después de este término

    # Determinar etiqueta basada en el score total
    # Ajustar umbrales si es necesario
    if total_score > 0.15: # Umbral ligeramente > 0 para ser positivo
        label = "positive"
    elif total_score < -0.15: # Umbral ligeramente < 0 para ser negativo
        label = "negative"
    else:
        label = "neutral"
        
    return {"label": label, "score": round(total_score, 2)}

def detect_mentioned_teams_mvp(text_to_analyze, equipos_dict):
    """
    Detecta equipos mencionados en un texto usando un diccionario de equipos y sus alias.
    Devuelve una lista de nombres canónicos de equipos encontrados.
    La búsqueda de alias es case-insensitive y busca coincidencias como palabras completas.
    """
    if not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
        return []
    if not equipos_dict:
        return []

    text_lower = text_to_analyze.lower()
    found_teams_canonical_names = set()

    # Ordenar los equipos por el alias más largo primero puede ayudar a evitar
    # que un alias corto (ej. "river") enmascare uno más largo (ej. "river plate").
    # Pero la lógica interna de los alias ya debería ser ordenada por longitud si es necesario.
    # Para este MVP, iteramos tal cual y confiamos en una buena definición de alias.

    for canonical_name, aliases in equipos_dict.items():
        for alias in aliases:
            alias_lower = alias.lower()
            # Usar expresiones regulares para buscar el alias como palabra completa
            # re.escape maneja caracteres especiales en el alias si los hubiera
            try:
                #  asegura que estamos buscando palabras completas
                # Ejemplo: si alias es "river", no coincidirá con "driver"
                pattern = r'\b' + re.escape(alias_lower) + r'\b'
                if re.search(pattern, text_lower):
                    found_teams_canonical_names.add(canonical_name)
                    break # Si encontramos un alias para este equipo, pasamos al siguiente equipo canónico
            except re.error as e:
                logging.warning(f"Regex error for alias '{alias_lower}' of team '{canonical_name}': {e}")
                # Continuar con el siguiente alias si hay un error de regex con el actual
                continue
                
    return list(found_teams_canonical_names)

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
        
        # --- Análisis de Sentimiento MVP ---
        if comment_dict["cleaned_text"]: # Solo analizar si hay texto limpio
            sentiment_result = analyze_sentiment_mvp(comment_dict["cleaned_text"])
            comment_dict["sentiment_analysis"] = sentiment_result
        else:
            comment_dict["sentiment_analysis"] = {"label": "neutral", "score": 0.0} # Default si no hay texto
        # --- Fin Análisis de Sentimiento ---

        # --- Detección de Equipos MVP ---
        if comment_dict["cleaned_text"]:
            mentioned_teams = detect_mentioned_teams_mvp(comment_dict["cleaned_text"], EQUIPOS_MVP)
            comment_dict["mentioned_teams"] = mentioned_teams
        else:
            comment_dict["mentioned_teams"] = [] # Default si no hay texto
        # --- Fin Detección de Equipos ---

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