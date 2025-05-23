#!/usr/bin/env python3
"""
Script para verificar que los datos han sido almacenados correctamente en Supabase.
Este script consulta la base de datos Supabase y muestra estadísticas sobre los comentarios almacenados.
"""

import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta
import time

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print(f"\n{'='*70}")
print(f"VERIFICACIÓN DE ALMACENAMIENTO EN SUPABASE")
print(f"{'='*70}")
print(f"URL: {SUPABASE_URL}")
print(f"KEY: {'*' * 10 + SUPABASE_KEY[-5:] if SUPABASE_KEY else 'No configurada'}")
print(f"{'='*70}\n")

# Verificar que las variables de entorno estén configuradas
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Las variables de entorno SUPABASE_URL y SUPABASE_KEY deben estar configuradas.")
    print("   Asegúrate de ejecutar el script con las variables de entorno correctas:")
    print("   source integration_test/run_database_writer_test.sh")
    sys.exit(1)

# Conectar a Supabase
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Conexión a Supabase establecida correctamente.")
except Exception as e:
    print(f"❌ Error al conectar a Supabase: {e}")
    sys.exit(1)

# Función para obtener comentarios recientes (últimas 24 horas)
def get_recent_comments(supabase_client):
    """Obtiene los comentarios almacenados en las últimas 24 horas"""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    
    try:
        response = supabase_client.table('comments').select('*').gte('created_at', yesterday_str).execute()
        if hasattr(response, 'data'):
            return response.data
        return []
    except Exception as e:
        print(f"❌ Error al consultar comentarios: {e}")
        return []

# Función para obtener menciones de equipos para un comentario
def get_team_mentions(supabase_client, comment_id):
    """Obtiene las menciones de equipos para un comentario específico"""
    try:
        response = supabase_client.table('mentioned_teams').select('*').eq('comment_id', comment_id).execute()
        if hasattr(response, 'data'):
            return response.data
        return []
    except Exception as e:
        print(f"❌ Error al consultar menciones de equipos: {e}")
        return []

# Función para obtener menciones de jugadores para un comentario
def get_player_mentions(supabase_client, comment_id):
    """Obtiene las menciones de jugadores para un comentario específico"""
    try:
        response = supabase_client.table('mentioned_players').select('*').eq('comment_id', comment_id).execute()
        if hasattr(response, 'data'):
            return response.data
        return []
    except Exception as e:
        print(f"❌ Error al consultar menciones de jugadores: {e}")
        return []

# Verificar comentarios recientes
print("📊 Buscando comentarios recientes en Supabase...")
comments = get_recent_comments(supabase)

if not comments:
    print("⚠️ No se encontraron comentarios recientes en Supabase.")
    print("   Posibles causas:")
    print("   1. El Database Writer no está en ejecución o no está conectado a Supabase")
    print("   2. No se han procesado comentarios recientemente")
    print("   3. Los comentarios procesados no se están almacenando correctamente")
    sys.exit(1)

# Mostrar estadísticas
print(f"\n📈 Se encontraron {len(comments)} comentarios recientes:")

# Estadísticas de sentimiento
sentiment_stats = {
    "positive": 0,
    "negative": 0,
    "neutral": 0
}

for comment in comments:
    sentiment = comment.get('sentiment_label')
    if sentiment in sentiment_stats:
        sentiment_stats[sentiment] += 1

print(f"\n🎭 Distribución de sentimiento:")
for sentiment, count in sentiment_stats.items():
    percentage = (count / len(comments)) * 100 if comments else 0
    print(f"  - {sentiment.capitalize()}: {count} ({percentage:.1f}%)")

# Eventos únicos
events = {}
for comment in comments:
    event_uuid = comment.get('event_uuid')
    if event_uuid:
        if event_uuid not in events:
            events[event_uuid] = {
                'count': 0,
                'home_team': comment.get('home_team'),
                'away_team': comment.get('away_team')
            }
        events[event_uuid]['count'] += 1

print(f"\n🏟️ Eventos detectados:")
for event_uuid, event_data in events.items():
    print(f"  - {event_data['home_team']} vs {event_data['away_team']}: {event_data['count']} comentarios")

# Mostrar algunos comentarios de ejemplo
print(f"\n📝 Ejemplos de comentarios almacenados:")
for i, comment in enumerate(comments[:5]):  # Mostrar solo los primeros 5
    print(f"\n{i+1}. \"{comment.get('original_text')}\"")
    print(f"   Sentimiento: {comment.get('sentiment_label')} (score: {comment.get('sentiment_score')})")
    print(f"   Autor: {comment.get('author_display_name')}")
    
    # Obtener menciones de equipos
    team_mentions = get_team_mentions(supabase, comment.get('id'))
    if team_mentions:
        print(f"   Equipos mencionados: {', '.join([tm.get('team_name') for tm in team_mentions])}")
    else:
        print(f"   Equipos mencionados: Ninguno")
    
    # Obtener menciones de jugadores
    player_mentions = get_player_mentions(supabase, comment.get('id'))
    if player_mentions:
        print(f"   Jugadores mencionados: {', '.join([f'{pm.get('player_name')} ({pm.get('player_team')})' for pm in player_mentions])}")
    else:
        print(f"   Jugadores mencionados: Ninguno")

if len(comments) > 5:
    print(f"\n... y {len(comments) - 5} comentarios más.")

print(f"\n{'='*70}")
print(f"✅ VERIFICACIÓN COMPLETADA EXITOSAMENTE")
print(f"{'='*70}")
