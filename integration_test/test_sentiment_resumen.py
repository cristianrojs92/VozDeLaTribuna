#!/usr/bin/env python3
"""
Script para probar directamente el analizador de sentimiento - versión resumida
"""

import sys
import os
import logging

# Configurar logging para reducir mensajes
logging.basicConfig(level=logging.ERROR)

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

# Probar cada comentario
print("=== PRUEBA DEL ANALIZADOR DE SENTIMIENTO (RESUMEN) ===")
print(f"Total de comentarios a analizar: {len(test_comments)}")
print("=============================================")

positive_count = 0
negative_count = 0
neutral_count = 0

# Analizar cada comentario
for i, comment in enumerate(test_comments):
    cleaned_text = clean_text(comment)
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
print("\n=== RESUMEN DE RESULTADOS ===")
print(f"Total comentarios: {len(test_comments)}")
print(f"Positivos: {positive_count} ({positive_count/len(test_comments)*100:.1f}%)")
print(f"Negativos: {negative_count} ({negative_count/len(test_comments)*100:.1f}%)")
print(f"Neutrales: {neutral_count} ({neutral_count/len(test_comments)*100:.1f}%)") 