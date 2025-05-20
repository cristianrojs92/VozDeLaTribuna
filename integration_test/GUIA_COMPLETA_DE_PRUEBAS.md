# Guía Completa de Pruebas - Voz de la Tribuna

Esta guía explica detalladamente el sistema de pruebas de integración para el procesador de comentarios del proyecto Voz de la Tribuna, describiendo cada componente y su interacción.

## 1. Introducción al Sistema

El proyecto "Voz de la Tribuna" procesa comentarios en tiempo real de aficionados durante partidos de fútbol. El sistema:

1. Captura comentarios de diversas fuentes (redes sociales, aplicaciones, etc.)
2. Procesa estos comentarios para extraer información valiosa:
   - Sentimiento general (positivo, negativo o neutral)
   - Equipos mencionados
   - Jugadores mencionados
3. Contextualiza esta información según el partido actual (equipos local y visitante)
4. Almacena los resultados para análisis posterior o visualización

## 2. Arquitectura del Sistema

### Componentes Principales:

```
┌─────────────┐    ┌───────┐    ┌────────────────────┐    ┌───────────┐
│ Productores │───►│ Redis │───►│ Procesador de      │───►│ Almacén   │
│ de datos    │    │ Stream│    │ Comentarios        │    │ de datos  │
└─────────────┘    └───────┘    └────────────────────┘    └───────────┘
```

1. **Productores de datos**: Capturan comentarios de diversas fuentes y los envían a Redis.
2. **Redis Stream**: Actúa como cola de mensajes, almacenando los comentarios hasta que son procesados.
3. **Procesador de Comentarios**: Lee los mensajes de Redis, analiza el texto, detecta entidades y sentimientos.
4. **Almacén de datos**: Donde se guardan los resultados procesados (aún en desarrollo).

## 3. Componentes Técnicos en Detalle

### 3.1 Redis como Sistema de Mensajería

Redis funciona como una "cinta transportadora" que mueve datos entre productores y consumidores:

- **Streams**: Listas cronológicas de mensajes que permiten múltiples consumidores.
- **Grupos de Consumidores**: Permiten que múltiples instancias del procesador trabajen juntas sin procesar mensajes duplicados.
- **Reconocimiento de Mensajes**: Cada mensaje debe ser "ack" (reconocido) después de procesarse correctamente.

Ejemplo de estructura de un mensaje en Redis:
```
┌─────────────────┐
│ ID: 1747732870093-0 │
├─────────────────┤
│ event_uuid: "7de40cbd-bb73-47a0-a001-e85751c4298d" │
│ stream_id: "independiente_huracán_test" │
│ platform_source: "test" │
│ author_display_name: "TestUser10" │
│ original_text: "Walter Mazzantti es un crack..." │
│ ... otros campos ... │
└─────────────────┘
```

### 3.2 Procesador de Comentarios

El procesador de comentarios (`comment_processor.py`) es el cerebro del sistema:

1. **Inicialización**:
   - Carga diccionarios de equipos y jugadores
   - Conecta con Redis
   - Crea o une a un grupo de consumidores

2. **Ciclo de Procesamiento**:
   - Lee mensajes nuevos del stream de Redis
   - Para cada mensaje:
     - Limpia y normaliza el texto
     - Realiza análisis de sentimiento
     - Detecta equipos mencionados
     - Detecta jugadores mencionados
     - Añade contexto del partido actual
     - Reconoce el mensaje como procesado

3. **Contexto de Partido**:
   - El procesador puede funcionar en modo general o en modo específico de partido
   - En modo específico, carga solo los equipos y jugadores relevantes para el partido, aumentando precisión

## 4. Sistema de Pruebas en Detalle

### 4.1 Estructura de las Pruebas

```
┌───────────────┐    ┌───────────┐    ┌──────────────────┐
│ Scripts de    │───►│ Redis     │───►│ Procesador de    │
│ Prueba (.py)  │    │ (Docker)  │    │ Comentarios      │
└───────────────┘    └───────────┘    └──────────────────┘
       ▲                                       │
       │                                       │
       └───────────────────────────────────────┘
          Verificación de resultados (logs/Redis)
```

### 4.2 Scripts de Configuración (.sh)

Los scripts `.sh` preparan el entorno de prueba:

1. **run_test_independiente_huracan.sh**:
   - Establece variables de entorno para el contexto del partido:
     - `MATCH_HOME_TEAM="Independiente"`
     - `MATCH_AWAY_TEAM="Huracán"`
     - `REDIS_STREAM_NAME="comment_stream:independiente_huracan_test"`
   - Proporciona instrucciones para ejecutar las pruebas

2. **run_test_custom_match.sh**:
   - Acepta dos argumentos: equipo local y equipo visitante
   - Genera dinámicamente un script Python para probar ese partido específico
   - Crea un nombre de stream único para evitar conflictos

### 4.3 Scripts de Prueba Python

Los scripts de prueba Python envían mensajes simulados a Redis:

1. **Conexión a Redis**:
   ```python
   r = redis.Redis(host='localhost', port=6379, decode_responses=True)
   ```

2. **Generación de Mensajes de Prueba**:
   - Crea comentarios realistas relacionados con el partido
   - Incluye menciones a equipos y jugadores específicos
   - Varía el tono (positivo, negativo, neutral)

3. **Envío a Redis**:
   ```python
   r.xadd(REDIS_STREAM_NAME, message)
   ```

### 4.4 Flujo Completo de los Datos

Para entender completamente el proceso, seguiremos un comentario desde su creación hasta su procesamiento:

1. **Creación del Comentario**:
   ```python
   {
     "original_text": "Cabral no puede dar un pase bien, horrible",
     "author_display_name": "TestUser11",
     # otros campos...
   }
   ```

2. **Envío a Redis**:
   - El script de prueba envía este mensaje al stream de Redis
   - Redis asigna un ID único: `1747732870600-0`

3. **Procesador Consume el Mensaje**:
   - El procesador detecta un nuevo mensaje
   - Lo extrae del stream para procesarlo

4. **Análisis del Contenido**:
   - Normaliza el texto: `"cabral no puede dar un pase bien, horrible"`
   - Realiza análisis de sentimiento: Resultado = negativo (-0.5)
   - Busca equipos mencionados: Ninguno encontrado
   - Busca jugadores mencionados: Encuentra "luciano cabral" del equipo "Independiente"

5. **Enriquecimiento**:
   - Añade el contexto del partido: `"home_team": "Independiente", "away_team": "Huracán"`
   - Genera un ID interno para seguimiento: `"internal_comment_id": "091bac5b-be3a-4264-986f-c533a0cb4b5a"`

6. **Finalización**:
   - Marca el mensaje como procesado (ACK)
   - Registra el resultado en logs
   - El mensaje no volverá a ser procesado

## 5. Guía Paso a Paso para Ejecutar Pruebas

### 5.1 Requisitos Previos

1. **Redis en Docker**:
   ```bash
   # Verificar que Redis está corriendo
   docker ps | grep redis
   ```

2. **Entorno Virtual Activado**:
   ```bash
   cd /Users/cristian/Proyectos/VozDeLaTribuna
   source .venv/bin/activate  # O el comando apropiado para tu sistema
   ```

### 5.2 Prueba del Partido Independiente vs Huracán

**Terminal 1: Configurar y Ejecutar el Procesador**
```bash
# Paso 1: Navegar al directorio del proyecto
cd /Users/cristian/Proyectos/VozDeLaTribuna

# Paso 2: Cargar las variables de entorno
source integration_test/run_test_independiente_huracan.sh

# Paso 3: Ejecutar el procesador de comentarios
python processors/comment_processor/comment_processor.py
```

**Terminal 2: Ejecutar el Script de Prueba**
```bash
# Paso 1: Navegar al directorio del proyecto
cd /Users/cristian/Proyectos/VozDeLaTribuna

# Paso 2: Configurar el stream de Redis
export REDIS_STREAM_NAME="comment_stream:independiente_huracan_test"

# Paso 3: Ejecutar el script de prueba
python integration_test/test_independiente_huracan.py
```

### 5.3 Prueba de un Partido Personalizado

**Terminal 1: Configurar y Ejecutar el Procesador**
```bash
# Paso 1: Navegar al directorio del proyecto
cd /Users/cristian/Proyectos/VozDeLaTribuna

# Paso 2: Crear el script de prueba para un partido específico
./integration_test/run_test_custom_match.sh "River Plate" "Boca Juniors"

# Paso 3: Ejecutar el procesador con las variables de entorno adecuadas
python processors/comment_processor/comment_processor.py
```

**Terminal 2: Ejecutar el Script de Prueba**
```bash
# Paso 1: Navegar al directorio del proyecto
cd /Users/cristian/Proyectos/VozDeLaTribuna

# Paso 2: Configurar el stream de Redis
export REDIS_STREAM_NAME="comment_stream:river_plate_boca_juniors_test"

# Paso 3: Ejecutar el script de prueba
python integration_test/test_river_plate_boca_juniors.py
```

## 6. Verificación de Resultados

### 6.1 Inspección Visual de Logs

En la terminal donde se ejecuta el procesador, deberías ver mensajes de log como:

```
2025-05-20 06:21:10,606 - INFO - Mensaje 1747732870600-0 procesado exitosamente (internal_id: 091bac5b-be3a-4264-986f-c533a0cb4b5a)
{
  "event_uuid": "7de40cbd-bb73-47a0-a001-e85751c4298d",
  "stream_id": "independiente_huracán_test",
  "platform_source": "test",
  "capture_timestamp_utc": "2025-05-20T09:21:10.599Z",
  "author_display_name": "TestUser11",
  "original_text": "Cabral no puede dar un pase bien, horrible",
  "source_comment_id": "test_comment_11",
  "platform_author_id": "user_11",
  "internal_comment_id": "091bac5b-be3a-4264-986f-c533a0cb4b5a",
  "processing_timestamp_utc": "2025-05-20T09:21:10.605Z",
  "cleaned_text": "cabral no puede dar un pase bien, horrible",
  "sentiment_analysis": {
    "label": "negative",
    "score": -0.5
  },
  "mentioned_teams": [],
  "mentioned_players": [
    {
      "nombre_canonico": "luciano cabral",
      "equipo": "Independiente"
    }
  ],
  "match_context": {
    "home_team": "Independiente",
    "away_team": "Huracán"
  }
}
```

### 6.2 Verificación Mediante Redis CLI

Comprobar los grupos de consumidores:

```bash
docker exec -it redis redis-cli XINFO GROUPS comment_stream:independiente_huracan_test
```

Resultado esperado:
```
1) 1) "name"
   2) "test_processing_group"
   3) "consumers"
   4) (integer) 1
   5) "pending"
   6) (integer) 0
   7) "last-delivered-id"
   8) "1747732874698-0"
```

Comprobar mensajes en el stream:

```bash
docker exec -it redis redis-cli XRANGE comment_stream:independiente_huracan_test - + COUNT 1
```

## 7. Análisis de Resultados

### 7.1 ¿Qué Observar?

1. **Carga de Diccionarios**:
   - El procesador debe cargar correctamente los diccionarios de equipos y jugadores
   - En modo contextual, solo debe cargar los equipos relevantes para el partido

2. **Detección de Entidades**:
   - Verificar que se detecten correctamente los equipos mencionados
   - Verificar que se detecten correctamente los jugadores mencionados

3. **Análisis de Sentimiento**:
   - Comprobar que los comentarios positivos, negativos y neutrales se clasifiquen correctamente

4. **Consumo de Mensajes**:
   - Todos los mensajes enviados deben ser procesados (el contador debe coincidir)
   - No debe haber mensajes pendientes al finalizar

### 7.2 Ejemplos de Éxito

1. **Detección correcta de jugador**:
   ```json
   "original_text": "Cabral no puede dar un pase bien, horrible",
   "mentioned_players": [
     {
       "nombre_canonico": "luciano cabral",
       "equipo": "Independiente"
     }
   ]
   ```

2. **Detección correcta de equipo y sentimiento**:
   ```json
   "original_text": "Walter Mazzantti es un crack, el único que intenta algo en el Globo",
   "sentiment_analysis": {
     "label": "positive",
     "score": 1.7
   },
   "mentioned_teams": [
     "Huracán"
   ]
   ```

## 8. Solución de Problemas Comunes

### 8.1 El Procesador No Conecta con Redis

**Síntoma**: El procesador muestra un error al conectar con Redis.

**Verificación**:
```bash
docker ps | grep redis
```

**Solución**: Si no está corriendo, iniciar Redis:
```bash
docker run -d --name redis -p 6379:6379 redis
```

### 8.2 El Procesador No Recibe Mensajes o No Crea Grupos de Consumidores

**Síntoma**: Se envían mensajes pero no aparecen en los logs del procesador o no se crea el grupo de consumidores.

**Verificación**: 
1. Comprobar que los nombres de stream coinciden:
```bash
echo $REDIS_STREAM_NAME
```

2. Verificar que las variables de entorno estén correctamente configuradas:
```bash
echo $MATCH_HOME_TEAM
echo $MATCH_AWAY_TEAM
```

**Solución**: 
1. Asegurarse de que el procesador y el script de prueba usen el mismo nombre de stream.
2. **Muy importante**: El procesador debe ejecutarse con las mismas variables de entorno que se configuraron con el script de preparación. Si el script configuró variables para "River Plate" vs "Boca Juniors", el procesador debe ejecutarse con esas mismas variables.

**Ejemplo de configuración correcta**:
```bash
# Configurar el entorno con el script adecuado primero
source integration_test/run_test_custom_match.sh "River Plate" "Boca Juniors"

# Luego ejecutar el procesador en la misma terminal
python processors/comment_processor/comment_processor.py
```

### 8.3 No Se Detectan Jugadores o Equipos

**Síntoma**: Los mensajes se procesan pero no se detectan entidades.

**Verificación**: Comprobar que los diccionarios se cargan correctamente (en los logs).

**Solución**:
1. Verificar que los nombres en el comentario coinciden con el diccionario
2. Verificar que las variables de entorno para el contexto del partido estén correctas

## 9. Avanzado: Cómo Funciona el Código

### 9.1 Carga de Diccionarios Contextual

```python
def load_players_dictionary(home_team=None, away_team=None):
    """
    Carga el diccionario de jugadores, opcionalmente filtrando por equipos del partido.
    """
    players_dict = {}
    players_count = 0
    
    # Dirección donde se encuentran los archivos JSON de jugadores
    dictionary_dir = os.path.join("data", "dictionaries", "team_players")
    
    # Si tenemos contexto de partido, solo cargamos los equipos relevantes
    teams_to_load = []
    if home_team and away_team:
        logging.info(f"Cargando jugadores para el partido: {home_team} vs {away_team}")
        for filename in os.listdir(dictionary_dir):
            if filename.endswith(".json"):
                team_id = filename.split(".")[0]
                team_name = team_id.replace("_", " ").title()
                
                if similar_team(team_name, home_team) or similar_team(team_name, away_team):
                    teams_to_load.append(filename)
    else:
        logging.info(f"Cargando todos los equipos y jugadores (sin contexto específico de partido)")
        # Sin contexto, cargamos todos los equipos
        teams_to_load = [f for f in os.listdir(dictionary_dir) if f.endswith('.json')]
```

### 9.2 Análisis de Sentimiento

```python
def analyze_sentiment_mvp(text):
    """
    Versión MVP simple del análisis de sentimiento.
    Retorna un objeto con 'label' (positive, negative, neutral) y 'score'.
    """
    # Palabras positivas y negativas
    positive_words = ["bueno", "excelente", "increíble", "golazo", "crack", "genio", "grande"]
    negative_words = ["malo", "pésimo", "horrible", "error", "fallo", "perdió", "desastre", "pierde"]
    
    # Normalizar texto
    text = text.lower()
    words = text.split()
    
    # Contar palabras positivas y negativas
    positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
    negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))
    
    # Calcular puntaje y etiqueta
    score = positive_count - negative_count
    
    if score > 0:
        return {"label": "positive", "score": float(score)}
    elif score < 0:
        return {"label": "negative", "score": float(score)}
    else:
        return {"label": "neutral", "score": 0.0}
```

### 9.3 Detección de Jugadores

```python
def detect_mentioned_players_mvp(text, players_dict):
    """
    Detecta menciones de jugadores en el texto usando un enfoque simple de coincidencia.
    """
    text = text.lower()
    mentioned_players = []
    
    for player, details in players_dict.items():
        if player.lower() in text:
            mentioned_players.append({
                "nombre_canonico": player.lower(),
                "equipo": details["equipo"]
            })
    
    return mentioned_players
```

## 10. Próximos Pasos

1. **Automatización Completa**: Convertir estas pruebas manuales en pruebas automatizadas con assertions.
2. **Dashboard de Resultados**: Crear una interfaz visual para revisar los resultados del procesamiento.
3. **Mejoras de Precisión**: Implementar técnicas más avanzadas de NLP para mejorar la detección.
4. **Escalabilidad**: Probar el sistema con volúmenes más grandes de mensajes.
5. **Integración Continua**: Añadir estas pruebas al pipeline de CI/CD.

---

Con esta guía, cualquier persona debería poder entender cómo funciona el sistema de procesamiento de comentarios, cómo se comunican sus componentes y cómo ejecutar las pruebas para verificar su correcto funcionamiento.