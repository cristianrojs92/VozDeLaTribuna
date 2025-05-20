# Manual de Pruebas de Integración - Voz de la Tribuna

Este manual describe los pasos para realizar pruebas de integración del procesador de comentarios con Redis, usando los scripts y herramientas disponibles en este directorio.

## Requisitos Previos

1. Redis funcionando (generalmente en un contenedor Docker)
2. Entorno virtual de Python activado
3. Todas las dependencias del proyecto instaladas

## Estructura de las Pruebas

Los scripts de prueba se encargan de:
1. Configurar el entorno con variables específicas para el partido
2. Generar mensajes de prueba para un partido específico
3. Enviar estos mensajes a un stream de Redis dedicado
4. Permitir que el procesador de comentarios consuma y procese estos mensajes

## Scripts Disponibles

### 1. `run_test_independiente_huracan.sh`

Este script configura el entorno para simular comentarios durante un partido entre Independiente y Huracán.

### 2. `run_test_custom_match.sh`

Este script permite configurar cualquier encuentro entre dos equipos, generando dinámicamente un script de prueba Python.

## Paso a Paso para Ejecutar Pruebas

### Prueba de Independiente vs Huracán

1. **Preparar el entorno**:
   ```bash
   cd /Users/cristian/Proyectos/VozDeLaTribuna
   source integration_test/run_test_independiente_huracan.sh
   ```

2. **Ejecutar el procesador de comentarios** (en una terminal):
   ```bash
   python processors/comment_processor/comment_processor.py
   ```

3. **Ejecutar el script de prueba** (en otra terminal):
   ```bash
   export REDIS_STREAM_NAME="comment_stream:independiente_huracan_test"
   python integration_test/test_independiente_huracan.py
   ```

### Prueba de Partido Personalizado

1. **Preparar el entorno**:
   ```bash
   cd /Users/cristian/Proyectos/VozDeLaTribuna
   ./integration_test/run_test_custom_match.sh "River Plate" "Boca Juniors"
   ```

2. **Ejecutar el procesador de comentarios** (en una terminal):
   ```bash
   python processors/comment_processor/comment_processor.py
   ```

3. **Ejecutar el script de prueba** (en otra terminal):
   ```bash
   export REDIS_STREAM_NAME="comment_stream:river_plate_boca_juniors_test"
   python integration_test/test_river_plate_boca_juniors.py
   ```

## Verificación de Resultados

Para verificar que los mensajes fueron procesados correctamente:

1. **Verificar grupos de consumidores**:
   ```bash
   docker exec -it redis redis-cli XINFO GROUPS <nombre_del_stream>
   ```
   Ejemplo:
   ```bash
   docker exec -it redis redis-cli XINFO GROUPS comment_stream:independiente_huracan_test
   ```

2. **Verificar mensajes en el stream**:
   ```bash
   docker exec -it redis redis-cli XRANGE <nombre_del_stream> - + COUNT 1
   ```
   Ejemplo:
   ```bash
   docker exec -it redis redis-cli XRANGE comment_stream:independiente_huracan_test - + COUNT 1
   ```

## Resultados Esperados

- El procesador debe crear un grupo de consumidores para el stream.
- Todos los mensajes enviados deben ser procesados correctamente.
- El procesamiento debe incluir:
  - Análisis de sentimiento
  - Detección de equipos mencionados
  - Detección de jugadores mencionados
  - Contexto del partido (equipos local y visitante)

## Ejemplos de Salida Exitosa

```
2025-05-20 06:21:10,103 - INFO - Acknowledged 1 messages: ['1747732870093-0']
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

## Problemas Comunes y Soluciones

1. **El procesador no conecta con Redis**:
   - Verificar que Redis esté corriendo: `docker ps | grep redis`
   - Verificar la configuración de conexión en el código

2. **No se crean grupos de consumidores**:
   - Verificar que el nombre del stream sea correcto
   - Verificar permisos en Redis
   - **Importante**: Asegurarse de que las variables de entorno estén correctamente configuradas. El procesador debe ejecutarse con las mismas variables que se usaron para configurar el test:
     ```bash
     # Para Independiente vs Huracán
     MATCH_HOME_TEAM=Independiente
     MATCH_AWAY_TEAM=Huracán
     REDIS_STREAM_NAME=comment_stream:independiente_huracan_test
     
     # Para River vs Boca
     MATCH_HOME_TEAM=River Plate
     MATCH_AWAY_TEAM=Boca Juniors
     REDIS_STREAM_NAME=comment_stream:river_plate_boca_juniors_test
     ```

3. **No se detectan equipos o jugadores**:
   - Verificar que los archivos JSON de equipos y jugadores estén correctamente cargados
   - Verificar que los nombres en los comentarios coincidan con los del diccionario

4. **El script de River vs Boca no genera grupo de consumidores**:
   - Asegurarse de usar las variables de entorno correctas al ejecutar el procesador
   - Verificar que se esté utilizando el script `run_test_custom_match.sh` para configurar el entorno

## Mejoras Futuras

- Agregar pruebas automatizadas con assertions
- Implementar un dashboard para visualizar los resultados
- Mejorar la detección de entidades con NLP más avanzado