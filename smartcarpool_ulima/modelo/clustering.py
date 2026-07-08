"""
Módulo de clustering para SmartCarpool ULima.
Contiene todo lo necesario para:
1. Cargar y preparar el dataset
2. Entrenar K-Means y DBSCAN
3. Comparar ambos algoritmos con silhouette score
4. Asignar un nuevo estudiante (formulario) al cluster más cercano
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


def cargar_datos(ruta_excel: str, n_muestra: int = 150) -> pd.DataFrame:
    """
    Carga el dataset y prepara las variables necesarias para el clustering:
    latitud, longitud y hora del viaje (a partir de 'Request Time').

    n_muestra: limitamos el dataset para que simule un tamaño realista
    de estudiantes de una universidad (150-300 según el alcance del curso).
    """
    df = pd.read_excel(ruta_excel)
    df = df.sample(n=min(n_muestra, len(df)), random_state=42).reset_index(drop=True)

    df["Hora"] = pd.to_datetime(df["Request Time"]).dt.hour + \
        pd.to_datetime(df["Request Time"]).dt.minute / 60

    # Renombramos para que se lea como "estudiantes" en vez de "rides"
    df = df.rename(columns={
        "Latitude Pickup": "Latitud",
        "Longitude Pickup": "Longitud",
        "Vehicle Type": "Tipo_Vehiculo",
    })

    return df[["Ride ID", "Latitud", "Longitud", "Hora", "Tipo_Vehiculo", "Day of Week"]]


def preparar_features(df: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    """Normaliza latitud, longitud y hora para que el clustering no se sesgue por escala."""
    X = df[["Latitud", "Longitud", "Hora"]].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, scaler


def entrenar_kmeans(X_scaled: np.ndarray, n_clusters: int = 6):
    modelo = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    etiquetas = modelo.fit_predict(X_scaled)
    return modelo, etiquetas


def entrenar_dbscan(X_scaled: np.ndarray, eps: float = 0.5, min_samples: int = 4):
    modelo = DBSCAN(eps=eps, min_samples=min_samples)
    etiquetas = modelo.fit_predict(X_scaled)
    return modelo, etiquetas


def comparar_algoritmos(X_scaled: np.ndarray, etiquetas_kmeans, etiquetas_dbscan) -> dict:
    """
    Devuelve el silhouette score de cada algoritmo (más cercano a 1 = mejor separación).
    DBSCAN puede generar ruido (-1); lo excluimos del cálculo de su score.
    """
    resultado = {}

    resultado["kmeans_score"] = silhouette_score(X_scaled, etiquetas_kmeans)
    resultado["kmeans_n_clusters"] = len(set(etiquetas_kmeans))

    mask = etiquetas_dbscan != -1
    if mask.sum() > 1 and len(set(etiquetas_dbscan[mask])) > 1:
        resultado["dbscan_score"] = silhouette_score(X_scaled[mask], etiquetas_dbscan[mask])
    else:
        resultado["dbscan_score"] = None
    resultado["dbscan_n_clusters"] = len(set(etiquetas_dbscan)) - (1 if -1 in etiquetas_dbscan else 0)
    resultado["dbscan_ruido"] = int((etiquetas_dbscan == -1).sum())

    return resultado


def asignar_nuevo_estudiante(lat, lon, hora, modelo_kmeans, scaler) -> int:
    """Dado el origen y horario de un estudiante nuevo, predice a qué cluster pertenece."""
    punto = scaler.transform([[lat, lon, hora]])
    cluster = modelo_kmeans.predict(punto)[0]
    return int(cluster)


def calcular_ahorro_co2(n_estudiantes_grupo: int) -> dict:
    """
    Estimación simple de sostenibilidad (indicador pedido en el alcance del proyecto).
    Supuesto: cada vehículo que se deja de usar evita ~2.3 kg CO2 por viaje (valor educativo, no oficial).
    """
    vehiculos_evitados = max(n_estudiantes_grupo - 1, 0)
    co2_evitado_kg = round(vehiculos_evitados * 2.3, 2)
    return {
        "vehiculos_evitados": vehiculos_evitados,
        "co2_evitado_kg": co2_evitado_kg,
    }
