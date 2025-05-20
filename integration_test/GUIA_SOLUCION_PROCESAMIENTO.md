# Guía de Solución para el Procesamiento de Mensajes

Esta guía te ayudará a solucionar el problema común donde los mensajes no son procesados correctamente entre el script de prueba y el procesador de comentarios.

## Problema Identificado

El principal problema ocurre cuando los mensajes enviados al stream de Redis no son recibidos por el procesador de comentarios. Esto generalmente se debe a una de las siguientes razones:

1. **Orden de ejecución incorrecto**: El procesador debe iniciarse antes que el script de prueba para crear el grupo de consumidores.
2. **Inconsistencia en nombres de streams**: Los nombres de streams difieren entre el procesador y el script de prueba.
3. **Estado residual en Redis**: Grupos de consumidores o streams en estado no deseado.

## Solución Implementada

Se han realizado los siguientes cambios:

1. **Mejora del script de prueba**: El script ahora verifica la existencia del grupo de consumidores antes de enviar mensajes.
2. **Script de limpieza mejorado**: Garantiza que el entorno de Redis esté limpio antes de comenzar.
3. **Corrección de compatibilidad**: Se ha mejorado el manejo de diferentes formatos de respuesta en las versiones de Redis.

## Notas sobre Compatibilidad con Redis

Se identificó un problema de compatibilidad entre diferentes versiones de Redis:

- En algunas versiones, las claves en la respuesta de `xinfo_groups` son bytes (ej. `b'name'`)
- En otras versiones, las claves son strings (ej. `'name'`)
- El script ahora maneja ambos casos, evitando el error: `AttributeError: 'NoneType' object has no attribute 'decode'`

## Pasos a Seguir para un Test Exitoso

Sigue estos pasos en el orden indicado:

### 1. Limpiar Redis antes de comenzar

```bash
cd /Users/cristian/Proyectos/VozDeLaTribuna && python integration_test/clean_redis.py
```

Este comando eliminará cualquier estado previo en Redis, incluyendo el stream y el grupo de consumidores.

### 2. Iniciar el procesador de comentarios

En una terminal:

```bash
cd /Users/cristian/Proyectos/VozDeLaTribuna && source integration_test/run_test_independiente_huracan.sh && python processors/comment_processor/comment_processor.py
```

Espera hasta ver el mensaje:
```
Consumer group 'test_processing_group' created for stream 'comment_stream:independiente_huracan_test'.
Starting consumer 'processor_instance_1' for group 'test_processing_group' on stream 'comment_stream:independiente_huracan_test'. Waiting for messages...
```

### 3. Ejecutar el script de prueba

En otra terminal:

```bash
cd /Users/cristian/Proyectos/VozDeLaTribuna && source integration_test/run_test_independiente_huracan.sh && python integration_test/test_independiente_huracan.py
```

El script verificará si el grupo de consumidores existe antes de enviar mensajes, y esperará si es necesario.

## Verificación

En la terminal del procesador, deberías ver:

- Mensajes de procesamiento para cada comentario enviado
- Detalles de análisis para cada comentario
- Confirmación de que los mensajes se están procesando ("Processing message XYZ...")

## Solución de Problemas Adicionales

Si aún experimentas problemas:

1. **Verifica que las variables de entorno coincidan**:
   ```bash
   echo $REDIS_STREAM_NAME
   echo $REDIS_CONSUMER_GROUP_NAME
   ```

2. **Monitorea Redis directamente**:
   ```bash
   redis-cli
   > XINFO STREAM comment_stream:independiente_huracan_test
   > XINFO GROUPS comment_stream:independiente_huracan_test
   > XINFO CONSUMERS comment_stream:independiente_huracan_test test_processing_group
   ```

3. **Verifica que no hay errores en los logs del procesador**:
   Busca excepciones o errores en la salida del procesador.

4. **Problemas de codificación**:
   Si ves errores relacionados con codificación o tipos de datos, considera que algunas versiones de Redis usan diferentes formatos de respuesta.

## Explicación Técnica

El problema principal suele ser de sincronización: cuando un grupo de consumidores se crea en Redis con `id='0'`, solo procesará mensajes que lleguen *después* de su creación. La solución implementada garantiza que el grupo exista antes de que se envíen los mensajes, asegurando que todos sean procesados correctamente. 