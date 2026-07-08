"""
Asistente Inteligente de Movilidad Universitaria (chatbot con Groq).

LO UNICO QUE DEBES HACER:
Pegar tu API key de Groq en el archivo .streamlit/secrets.toml
(ver INSTRUCCIONES.md, seccion "Configurar el chatbot con Groq").
Groq es gratis y NO pide tarjeta de credito.
"""

import streamlit as st
from groq import Groq

MODELO_GROQ = "openai/gpt-oss-20b"  # modelo rapido y gratuito en el free tier de Groq


def responder_pregunta(pregunta: str, contexto_cluster: dict) -> str:
    """
    Envia la pregunta del estudiante a Groq junto con el contexto de su
    asignacion (cluster, numero de companeros, ahorro CO2, etc.) para que
    el chatbot explique la recomendacion de forma personalizada.
    """
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return ("No configuraste tu API key de Groq todavia. "
                "Revisa el archivo INSTRUCCIONES.md, seccion 'Configurar el chatbot con Groq'.")

    if not pregunta or not pregunta.strip():
        return "Escribe una pregunta primero."

    client = Groq(api_key=api_key)

    prompt_sistema = f"""
Eres el Asistente Inteligente de Movilidad Universitaria de SmartCarpool ULima.
Ayudas a estudiantes a entender por que fueron agrupados para compartir vehiculo,
y respondes dudas sobre rutas, horarios y beneficios ambientales del carpooling.

Contexto del estudiante actual:
- Grupo asignado: {contexto_cluster.get('grupo')}
- Numero de companeros en su grupo: {contexto_cluster.get('n_compañeros')}
- Vehiculos evitados si comparten viaje: {contexto_cluster.get('vehiculos_evitados')}
- CO2 evitado estimado (kg): {contexto_cluster.get('co2_evitado_kg')}

Responde en espanol, de forma breve, clara y amigable (maximo 4-5 lineas).
"""

    try:
        respuesta = client.chat.completions.create(
            model=MODELO_GROQ,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": pregunta},
            ],
            max_tokens=250,
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        return f"Ocurrio un error al conectar con Groq: {e}"
