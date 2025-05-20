# Guía de Solución para el Procesamiento de Mensajes

Esta guía te ayudará a solucionar problemas comunes en el procesamiento de mensajes entre los scripts de prueba y el procesador de comentarios.

## Problemas Identificados y Soluciones

### 1. Problemas de Comunicación con Redis

**Problema**: Los mensajes enviados al stream de Redis no son recibidos por el procesador de comentarios.

**Causas comunes**:
- Orden de ejecución incorrecto
- Inconsistencia en nombres de streams
- Estado residual en Redis
- Problemas de codificación en las claves de Redis

**Solución**:
1. **Limpiar Redis antes de comenzar**:
   ```bash
   cd /Users/cristian/Proyectos/VozDeLaTribuna && python integration_test/clean_redis.py
   ```

2. **Verificar consistencia en los nombres**:
   - El nombre del stream debe ser el mismo en el productor y el procesador
   - El nombre del grupo de consumidores debe coincidir

3. **Iniciar el procesador antes que el script de prueba**:
   ```bash
   cd /Users/cristian/Proyectos/VozDeLaTribuna && source integration_test/run_test_independiente_huracan.sh && python processors/comment_processor/comment_processor.py
   ```

### 2. Problemas con la Detección de Entidades

**Problema**: Los equipos o jugadores no son detectados correctamente en los mensajes.

**Causas comunes**:
- Formato incorrecto en el diccionario de retorno
- Error en la carga de diccionarios de jugadores o equipos
- Falta de configuración del contexto de partido

**Solución**:
1. **Verificar la carga de diccionarios**:
   - Revisar los logs para confirmar que se cargaron correctamente
   - Validar que los archivos JSON de jugadores existen y están bien formateados

2. **Revisar la configuración de contexto**:
   ```bash
   echo $MATCH_HOME_TEAM
   echo $MATCH_AWAY_TEAM
   echo $MATCH_CONTEXT_ENABLED
   ```

3. **Asegurar formato correcto de resultados**:
   - `mentioned_teams` debe ser un array de objetos con propiedad "name"
   - `mentioned_players` debe ser un array de objetos con propiedades "name" y "team"

### 3. Problemas con el Análisis de Sentimiento

**Problema**: El análisis de sentimiento devuelve resultados inesperados (p.ej. frases positivas marcadas como negativas).

**Causas comunes**:
- Palabras clasificadas incorrectamente en los diccionarios
- Errores en el algoritmo de detección
- Limitaciones en el bucle de análisis

**Solución**:
1. **Revisar y ajustar diccionarios**:
   - Términos como "dominar" en fútbol son positivos en el contexto adecuado
   - Revisar las puntuaciones asignadas a cada término

2. **Resolver problemas de bucle**:
   - Se han implementado límites de iteración para evitar bucles infinitos
   - La advertencia "Bucle interno alcanzó límite de 100 para el término" indica posible problema

3. **Considerar contexto específico de fútbol**:
   - Frases como "dominar la posesión" deberían agregarse explícitamente como positivas
   - El análisis palabra por palabra puede fallar en algunas expresiones deportivas

## Verificación de Procesamiento Correcto

El procesador mejorado ahora muestra información detallada sobre el procesamiento:

```
2025-05-20 10:37:06 - INFO - 🔄 INICIANDO PROCESAMIENTO DEL MENSAJE: 1747748226293-0
2025-05-20 10:37:06 - INFO - 📦 PAYLOAD RECIBIDO: {...}
2025-05-20 10:37:06 - INFO - 📝 TEXTO ORIGINAL: 'Qué partido aburrido, ninguno propone nada'
2025-05-20 10:37:06 - INFO - 🧹 TEXTO LIMPIO: 'qué partido aburrido, ninguno propone nada'
2025-05-20 10:37:06 - INFO - 😀 SENTIMIENTO: negative (score: -81.6)
2025-05-20 10:37:06 - INFO - ⚽ NO SE DETECTARON EQUIPOS
2025-05-20 10:37:06 - INFO - 👤 NO SE DETECTARON JUGADORES
2025-05-20 10:37:06 - INFO - ✅ Mensaje procesado exitosamente (internal_id: cb8da72f-224e-4659-8e81-b7e46adba7fe)
```

También se muestra un resumen por lotes:
```
2025-05-20 10:37:06 - INFO - ✅ ACK para 1 mensajes. Resumen lote #250: 1 procesados, 60 exitosos total, 0 fallidos total.
```

## Manejo Robusto de Errores

El procesador ahora implementa un manejo robusto de errores:

1. **Protección contra fallos en deserialización**:
   - Errores en la decodificación JSON no detienen todo el proceso
   - Se registran errores detallados para depuración

2. **Protección en componentes independientes**:
   - Análisis de sentimiento, detección de equipos y jugadores en bloques try-except separados
   - Un fallo en un componente no impide el procesamiento de los demás

3. **Reconocimiento de mensajes con error**:
   - Los mensajes que producen error son reconocidos (ACK) para evitar que queden pendientes
   - Se mantiene estadística de mensajes fallidos vs. exitosos

## Pasos a Seguir para un Test Exitoso

1. **Limpiar Redis**:
   ```bash
   cd /Users/cristian/Proyectos/VozDeLaTribuna && python integration_test/clean_redis.py
   ```

2. **Iniciar el procesador**:
   ```bash
   cd /Users/cristian/Proyectos/VozDeLaTribuna && source integration_test/run_test_independiente_huracan.sh && python processors/comment_processor/comment_processor.py
   ```

3. **Ejecutar el script de prueba** (en otra terminal):
   ```bash
   cd /Users/cristian/Proyectos/VozDeLaTribuna && source integration_test/run_test_independiente_huracan.sh && python integration_test/test_independiente_huracan.py
   ```

4. **Verificar procesamiento correcto**:
   - Observar los logs decorados con emojis
   - Comprobar que todos los mensajes son procesados
   - Verificar que los contadores de mensajes coinciden con lo esperado

## Solución de problemas con el Análisis de Sentimiento

Si necesitas ajustar la clasificación de sentimientos para casos específicos como "los diablos rojos dominan la posesión" (clasificado incorrectamente como negativo), considera:

1. **Revisar el diccionario de términos**:
   - Añadir términos como "dominar", "posesión" al diccionario positivo
   - Ajustar las puntuaciones de sentimiento para términos deportivos

2. **Añadir frases completas**:
   - Complementar el análisis palabra por palabra con un diccionario de frases completas
   - Añadir expresiones como "dominar la posesión" como entradas positivas

3. **Mejorar el sistema de negaciones**:
   - Revisar el alcance de las negaciones para evitar falsos negativos/positivos
   - Refinar la ventana de contexto para negaciones

Las mejoras implementadas aseguran que, incluso con estas limitaciones, el procesador pueda continuar funcionando y procese todos los mensajes sin detenerse.

## Compatibilidad con Redis

Las soluciones implementadas manejan diferencias entre versiones de Redis:
- Soporte para claves como bytes (`b'name'`) o como strings (`'name'`)
- Manejo de diferentes formatos en respuestas de comandos como `xinfo_groups`
- Detección y creación adecuada de grupos de consumidores independientemente de la versión 