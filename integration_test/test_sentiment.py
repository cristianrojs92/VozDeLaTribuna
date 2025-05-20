#!/usr/bin/env python3
"""
Script para probar directamente el analizador de sentimiento.
"""

import sys
import os

# Añadir el directorio de los procesadores al path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'processors/comment_processor'))

# Importar la función de análisis de sentimiento
from comment_processor import analyze_sentiment_mvp, clean_text

# Lista de comentarios de prueba tomados del test de Independiente vs Huracán
test_comments = [
    # Menciones a equipos (usando diferentes alias)
    "El Rojo está jugando increíble este torneo, son una máquina",
    "Los Diablos Rojos dominan la posesión",
    "Independiente presiona mucho",
    "El Globo está muy defensivo hoy",
    "Huracán no puede salir de su área",
    "El Quemero hoy no encuentra la pelota",
    
    # Menciones a jugadores de Independiente (con sentimiento)
    "Rey de Independiente está atento en el arco",
    "Gran partido de Rodrigo Rey, salvó al Rojo",
    "Laso es un desastre en la defensa del Rojo",
    "Saltita González se está comiendo la cancha",
    
    # Menciones a jugadores de Huracán (con sentimiento)
    "Walter Mazzantti es un crack, el único que intenta algo en el Globo",
    "Cabral no puede dar un pase bien, horrible",
    "Gran atajada de Chaves para el Globo",
    
    # Comentarios complejos con múltiples entidades
    "Mazzantti del Globo está imparable pero Rey del Rojo le ataja todo",
    "El partido está aburrido, ni Independiente ni Huracán generan peligro",
    
    # Ambigüedad que debería resolverse con el contexto (Marcos Rojo de Boca vs el Rojo)
    "El rojo tiene que mejorar mucho en defensa",
    "A Rojo le falta intensidad en el mediocampo",
    
    # Comentarios neutrales o ambiguos
    "El árbitro está dejando jugar",
    "Qué partido aburrido, ninguno propone nada",
    "El VAR debería revisar esa jugada"
]

# Añadimos frases de prueba adicionales más específicas para el análisis de sentimiento
additional_test_comments = [
    # Frases positivas claras
    "Golazo increíble",
    "Es un crack total",
    "Partidazo, impresionante lo que está jugando",
    "Qué bien están jugando, son una máquina",
    
    # Frases negativas claras
    "Qué horrible ese pase",
    "Es un desastre este equipo",
    "Malísimo el árbitro",
    "No dan una, son un desastre",
    
    # Frases con términos específicos del fútbol
    "Se está comiendo la cancha", # Expresión positiva que no parece estar en el diccionario
    "Gran atajada", # Positiva específica de arqueros
    "Salvó al equipo", # Positiva
    "No encuentra la pelota", # Negativa
    "Está muy defensivo", # Neutral
    "Dominan la posesión", # Positiva
    "No puede salir de su área", # Negativa
    "Presiona mucho", # Positiva
    "Está atento en el arco", # Positiva
    "Le falta intensidad", # Negativa
    "Tiene que mejorar mucho", # Negativa
    "Es el único que intenta algo", # Mixta (negativa para el equipo, positiva para el jugador)
    "No puede dar un pase bien", # Negativa
    "Ninguno propone nada" # Negativa
]

test_comments.extend(additional_test_comments)

# Probar cada comentario
print("=== PRUEBA DEL ANALIZADOR DE SENTIMIENTO ===")
print(f"Total de comentarios a analizar: {len(test_comments)}")
print("=============================================")

positive_count = 0
negative_count = 0
neutral_count = 0

for i, comment in enumerate(test_comments):
    # Limpiar el texto
    cleaned_text = clean_text(comment)
    
    # Analizar sentimiento
    result = analyze_sentiment_mvp(cleaned_text)
    
    # Contar por categoría
    if result["label"] == "positive":
        positive_count += 1
    elif result["label"] == "negative":
        negative_count += 1
    else:
        neutral_count += 1
    
    # Mostrar resultado
    print(f"[{i+1}/{len(test_comments)}] {result['label'].upper()} (score: {result['score']}): {comment}")

# Mostrar resumen
print("\n=== RESUMEN ===")
print(f"Total comentarios: {len(test_comments)}")
print(f"Positivos: {positive_count} ({positive_count/len(test_comments)*100:.1f}%)")
print(f"Negativos: {negative_count} ({negative_count/len(test_comments)*100:.1f}%)")
print(f"Neutrales: {neutral_count} ({neutral_count/len(test_comments)*100:.1f}%)")

# Mostrar los diccionarios utilizados
from comment_processor import DICCIONARIO_POSITIVAS_MVP, DICCIONARIO_NEGATIVAS_MVP

print("\n=== DICCIONARIO DE TÉRMINOS POSITIVOS (muestra) ===")
for i, (term, score) in enumerate(sorted(DICCIONARIO_POSITIVAS_MVP.items(), key=lambda x: x[1], reverse=True)[:20]):
    print(f"{term}: {score}")

print("\n=== DICCIONARIO DE TÉRMINOS NEGATIVOS (muestra) ===")
for i, (term, score) in enumerate(sorted(DICCIONARIO_NEGATIVAS_MVP.items(), key=lambda x: x[1])[:20]):
    print(f"{term}: {score}")

# Prueba términos específicos
print("\n=== TÉRMINOS ESPECÍFICOS QUE FALTAN EN EL DICCIONARIO ===")
terms_to_check = [
    "increíble", "increible", "imparable", "atento", "dominan", "presiona", 
    "salvó", "atajada", "comiendo la cancha", "gran partido",
    "encuentra", "defensivo", "intensidad", "mejorar", "propone"
]

for term in terms_to_check:
    positivo = term in DICCIONARIO_POSITIVAS_MVP
    negativo = term in DICCIONARIO_NEGATIVAS_MVP
    if positivo:
        score = DICCIONARIO_POSITIVAS_MVP[term]
        category = "POSITIVO"
    elif negativo:
        score = DICCIONARIO_NEGATIVAS_MVP[term]
        category = "NEGATIVO"
    else:
        score = "N/A"
        category = "NO ENCONTRADO"
    
    print(f"'{term}': {category} (score: {score})") 