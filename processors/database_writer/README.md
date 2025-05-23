# Database Writer para VozDeLaTribuna

Este componente es responsable de consumir los comentarios procesados del stream de Redis y almacenarlos en la base de datos Supabase.

## Funcionalidad

- Conecta con Redis y crea un grupo de consumidores
- Lee comentarios procesados del stream `comment_stream:processed`
- Almacena los comentarios y sus metadatos en la base de datos Supabase
- Mantiene un registro detallado de las operaciones

## Configuración

1. Copia el archivo `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edita el archivo `.env` y configura:
   - Las credenciales de Supabase (URL y clave anónima)
   - La configuración de Redis (host, puerto, nombre del stream)
   - Los parámetros de procesamiento según sea necesario

## Requisitos

1. Crea y activa un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

1. Asegúrate de que Redis esté en ejecución y configurado correctamente.

2. Asegúrate de que el Comment Processor esté en ejecución y configurado para enviar a `comment_stream:processed`.

3. Inicia el Database Writer:

```bash
python database_writer.py
```

4. Para detener la ejecución, presiona Ctrl+C.

## Integración con el sistema

Este componente espera recibir mensajes del Comment Processor a través de Redis. El Comment Processor debe ser modificado para enviar los comentarios procesados al stream `comment_stream:processed`.

## Estructura de los datos

Los comentarios son almacenados en las siguientes tablas de Supabase:

1. `comments`: La tabla principal con los datos del comentario
2. `mentioned_teams`: Referencias a equipos mencionados en el comentario
3. `mentioned_players`: Referencias a jugadores mencionados en el comentario

Las métricas agregadas se actualizan automáticamente mediante triggers de base de datos configurados en Supabase.
