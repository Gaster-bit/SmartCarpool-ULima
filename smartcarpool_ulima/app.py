"""
SmartCarpool ULima
Prototipo de aplicación web para agrupar estudiantes con rutas y horarios
similares mediante clustering (K-Means y DBSCAN), con visualización en mapa
y un chatbot de movilidad universitaria basado en LLM.

Ejecutar localmente con:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium

from modelo.clustering import (
    cargar_datos,
    preparar_features,
    entrenar_kmeans,
    entrenar_dbscan,
    comparar_algoritmos,
    asignar_nuevo_estudiante,
    calcular_ahorro_co2,
)
from chatbot.asistente import responder_pregunta

st.set_page_config(page_title="SmartCarpool ULima", page_icon="🚗", layout="wide")

# Ruta absoluta basada en la ubicación de este archivo (app.py), NO en el
# directorio desde donde se ejecuta el proceso. Esto evita el error
# "FileNotFoundError" cuando se despliega en Streamlit Cloud, donde el
# repositorio puede tener una carpeta extra antes de app.py.
CARPETA_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_DATASET = os.path.join(CARPETA_ACTUAL, "data", "Ride_Sharing_Dataset.xlsx")

# ---------------------------------------------------------------------------
# Carga y entrenamiento (se cachea para no recalcular en cada clic)
# ---------------------------------------------------------------------------
@st.cache_resource
def preparar_modelos():
    df = cargar_datos(RUTA_DATASET, n_muestra=150)
    X_scaled, scaler = preparar_features(df)

    modelo_km, etiquetas_km = entrenar_kmeans(X_scaled, n_clusters=6)
    modelo_db, etiquetas_db = entrenar_dbscan(X_scaled, eps=0.5, min_samples=4)

    comparacion = comparar_algoritmos(X_scaled, etiquetas_km, etiquetas_db)

    df["Cluster_KMeans"] = etiquetas_km
    df["Cluster_DBSCAN"] = etiquetas_db

    return df, modelo_km, scaler, comparacion


df, modelo_km, scaler, comparacion = preparar_modelos()

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.title("🚗 SmartCarpool ULima")
st.caption("Asistente inteligente de movilidad universitaria — agrupamos estudiantes con rutas y horarios similares.")

tab1, tab2, tab3 = st.tabs(["📝 Registrarme", "📊 Resultados del clustering", "💬 Chatbot"])

# ---------------------------------------------------------------------------
# TAB 1: Formulario del estudiante
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Regístrate para encontrar tu grupo de viaje")

    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitud de tu origen", value=-12.0864, format="%.6f")
        lon = st.number_input("Longitud de tu origen", value=-76.9950, format="%.6f")
        hora = st.slider("Hora de ingreso a la universidad", 0.0, 23.5, 7.5, step=0.5)
    with col2:
        tiene_vehiculo = st.radio("¿Dispones de vehículo?", ["Sí", "No"])
        asientos = st.number_input("Número de asientos disponibles", min_value=0, max_value=8, value=0)

    if st.button("Buscar mi grupo", type="primary"):
        # Aquí SOLO calculamos y guardamos en memoria de sesión.
        # No dibujamos nada todavía (eso pasa más abajo, fuera del botón),
        # para que el resultado no desaparezca cuando el mapa provoque un rerun.
        cluster_asignado = asignar_nuevo_estudiante(lat, lon, hora, modelo_km, scaler)
        compañeros = df[df["Cluster_KMeans"] == cluster_asignado]
        n_compañeros = len(compañeros)
        ahorro = calcular_ahorro_co2(n_compañeros)

        st.session_state["ultimo_resultado"] = {
            "grupo": cluster_asignado,
            "n_compañeros": n_compañeros,
            "vehiculos_evitados": ahorro["vehiculos_evitados"],
            "co2_evitado_kg": ahorro["co2_evitado_kg"],
            "lat": lat,
            "lon": lon,
            "compañeros_lat_lon": compañeros[["Latitud", "Longitud"]].values.tolist(),
        }

    # Esta parte se dibuja SIEMPRE que exista un resultado guardado,
    # sin importar si el botón sigue "presionado" o no. Así no desaparece.
    if "ultimo_resultado" in st.session_state:
        r = st.session_state["ultimo_resultado"]

        st.success(f"✅ Fuiste asignado al **Grupo {r['grupo']}**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Compañeros en tu grupo", r["n_compañeros"])
        c2.metric("Vehículos evitados", r["vehiculos_evitados"])
        c3.metric("CO₂ evitado estimado", f"{r['co2_evitado_kg']} kg")

        st.markdown("#### Mapa de tu grupo")
        mapa = folium.Map(location=[r["lat"], r["lon"]], zoom_start=11)
        folium.Marker([r["lat"], r["lon"]], tooltip="Tú", icon=folium.Icon(color="red")).add_to(mapa)
        for lat_c, lon_c in r["compañeros_lat_lon"]:
            folium.CircleMarker(
                [lat_c, lon_c],
                radius=5, color="blue", fill=True,
                tooltip=f"Compañero - Grupo {r['grupo']}",
            ).add_to(mapa)
        st_folium(mapa, width=900, height=450, key="mapa_grupo")

# ---------------------------------------------------------------------------
# TAB 2: Resultados del clustering (K-Means vs DBSCAN)
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Comparación K-Means vs DBSCAN")

    c1, c2 = st.columns(2)
    c1.metric("Silhouette Score K-Means", f"{comparacion['kmeans_score']:.3f}")
    c1.metric("Clusters formados (K-Means)", comparacion["kmeans_n_clusters"])

    if comparacion["dbscan_score"] is not None:
        c2.metric("Silhouette Score DBSCAN", f"{comparacion['dbscan_score']:.3f}")
    else:
        c2.metric("Silhouette Score DBSCAN", "N/A")
    c2.metric("Clusters formados (DBSCAN)", comparacion["dbscan_n_clusters"])
    c2.metric("Puntos de ruido (DBSCAN)", comparacion["dbscan_ruido"])

    mejor = "K-Means" if comparacion["kmeans_score"] >= (comparacion["dbscan_score"] or 0) else "DBSCAN"
    st.info(f"📌 Según el silhouette score, **{mejor}** produjo el mejor agrupamiento en este dataset.")

    st.markdown("#### Distribución de estudiantes por cluster (K-Means)")
    conteo = df["Cluster_KMeans"].value_counts().sort_index()
    st.bar_chart(conteo)

    st.markdown("#### Mapa general de todos los clusters (K-Means)")
    mapa_general = folium.Map(location=[df["Latitud"].mean(), df["Longitud"].mean()], zoom_start=2)
    colores = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue"]
    for _, fila in df.iterrows():
        folium.CircleMarker(
            [fila["Latitud"], fila["Longitud"]],
            radius=4,
            color=colores[int(fila["Cluster_KMeans"]) % len(colores)],
            fill=True,
            tooltip=f"Cluster {fila['Cluster_KMeans']}",
        ).add_to(mapa_general)
    st_folium(mapa_general, width=900, height=450)

    with st.expander("Ver tabla de datos usada"):
        st.dataframe(df)

# ---------------------------------------------------------------------------
# TAB 3: Chatbot
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("💬 Asistente de Movilidad Universitaria")

    if "ultimo_resultado" not in st.session_state:
        st.warning("Primero regístrate en la pestaña '📝 Registrarme' para que el chatbot tenga contexto sobre tu grupo.")
    else:
        pregunta = st.text_input("Escribe tu pregunta (ej: ¿Por qué fui asignado a este grupo?)")
        if st.button("Preguntar"):
            with st.spinner("Pensando..."):
                respuesta = responder_pregunta(pregunta, st.session_state["ultimo_resultado"])
            st.markdown(f"**Asistente:** {respuesta}")
