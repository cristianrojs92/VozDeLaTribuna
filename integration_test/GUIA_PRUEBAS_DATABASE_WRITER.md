# Guía de Pruebas End-to-End con Database Writer

Esta guía explica cómo ejecutar pruebas completas del sistema VozDeLaTribuna, incluyendo el almacenamiento de datos en Supabase.

## Componentes del Sistema

El sistema completo consta de tres componentes principales:

1. **YouTube Producer**: Captura comentarios de YouTube Live y los envía a Redis
2. **Comment Processor**: Procesa los comentarios (sentimiento, equipos, jugadores) y los envía a otro stream de Redis
3. **Database Writer**: Almacena los comentarios procesados en Supabase

## Flujo de Datos

```
YouTube Producer → Redis (comment_stream:live) → Comment Processor 
                                                       ↓
                                Redis (comment_stream:processed) → Database Writer → Supabase
```

## Opciones de Prueba

### 1. Prueba Automática Completa

Para ejecutar una prueba completa end-to-end que configure el entorno, inicie todos los componentes y verifique los resultados:

```bash
cd /Users/cristian/Proyectos/VozDeLaTribuna
./integration_test/ejecutar_test_completo_con_db.sh
```

Este script:
- Limpia Redis
- Configura el entorno para el partido Independiente vs Huracán
- Inicia el Comment Processor y el Database Writer
- Ejecuta el script de prueba que envía comentarios
- Verifica que los comentarios se almacenen correctamente en Supabase
- Detiene todos los procesos
- Guarda logs detallados en `integration_test/logs/`

### 2. Prueba Manual Paso a Paso

Si prefieres ejecutar los componentes manualmente para mayor control:

#### Terminal 1: Comment Processor
```bash
cd /Users/cristian/Proyectos/VozDeLaTribuna
source integration_test/run_test_independiente_huracan.sh
python processors/comment_processor/comment_processor.py
```

#### Terminal 2: Database Writer
```bash
cd /Users/cristian/Proyectos/VozDeLaTribuna
source integration_test/run_database_writer_test.sh
python processors/database_writer/database_writer.py
```

#### Terminal 3: Script de Prueba
```bash
cd /Users/cristian/Proyectos/VozDeLaTribuna
source integration_test/run_test_independiente_huracan.sh
python integration_test/test_independiente_huracan.py
```

#### Terminal 4: Verificación de Almacenamiento
```bash
cd /Users/cristian/Proyectos/VozDeLaTribuna
source integration_test/run_database_writer_test.sh
python integration_test/verify_supabase_storage.py
```

## Verificación de Resultados

### Logs

Cada componente genera sus propios logs:

- **Comment Processor**: `processors/comment_processor/logs/comment_processor_YYYY-MM-DD.log`
- **Database Writer**: `processors/database_writer/logs/database_writer_YYYY-MM-DD.log`
- **Prueba Automática**: `integration_test/logs/test_completo_YYYYMMDD_HHMMSS.log`

### Supabase

Para verificar los datos en Supabase:

1. Ejecuta el script de verificación:
   ```bash
   python integration_test/verify_supabase_storage.py
   ```

2. O accede directamente al panel de control de Supabase:
   - URL: https://cxnqyytqsnjcmpbijczp.supabase.co
   - Navega a Table Editor → comments

## Solución de Problemas

### El Comment Processor no envía a `comment_stream:processed`

- Verifica que la variable `REDIS_PROCESSED_STREAM` esté configurada correctamente
- Comprueba los logs del Comment Processor por errores al enviar al stream

### El Database Writer no consume mensajes

- Verifica que el Comment Processor esté enviando mensajes al stream correcto
- Comprueba que las variables de Redis estén configuradas igual en ambos componentes
- Verifica los logs del Database Writer por errores de conexión

### Los datos no aparecen en Supabase

- Verifica que las credenciales de Supabase (`SUPABASE_URL` y `SUPABASE_KEY`) sean correctas
- Comprueba los logs del Database Writer por errores al insertar datos
- Verifica que el esquema de la base de datos en Supabase coincida con el esperado

## Recursos Adicionales

- **Guía Completa de Pruebas**: Ver `GUIA_COMPLETA_DE_PRUEBAS.md`
- **Solución de Problemas de Procesamiento**: Ver `GUIA_SOLUCION_PROCESAMIENTO.md`
