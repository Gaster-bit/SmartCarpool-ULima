# SmartCarpool ULima — Instrucciones finales

Todo el sistema ya está construido: dataset, clustering (K-Means y DBSCAN),
mapa interactivo, formulario y chatbot. Solo te faltan **2 pasos sencillos**.

## Paso 1: Probarlo en tu computadora

1. Descarga la carpeta `smartcarpool_ulima` completa.
2. Abre una terminal dentro de esa carpeta.
3. Instala las librerías:
   ```
   pip install -r requirements.txt
   ```
4. Ejecuta la app:
   ```
   streamlit run app.py
   ```
5. Se abrirá en tu navegador en `http://localhost:8501`.

En este punto, todo funcionará **excepto el chatbot** (te dirá que falta la API key). Eso es normal, lo arreglas en el paso 2.

## Paso 2: Configurar el chatbot con Groq (gratis, sin tarjeta)

Groq te deja usar modelos de IA (tipo Llama/GPT-OSS) totalmente gratis,
sin pedir tarjeta de crédito. Es la opción más simple para este proyecto.

1. Entra a https://console.groq.com/ e inicia sesión (puedes usar tu
   cuenta de Google directamente, no necesitas crear contraseña nueva).
2. En el menú de la izquierda, click en **"API Keys"**.
3. Click en **"Create API Key"**, ponle un nombre (ej: "smartcarpool") y
   click en crear. Copia la clave que te muestra (empieza con `gsk_...`).
   ⚠️ Solo te la muestra una vez, cópiala de inmediato.
4. Dentro de la carpeta del proyecto, crea una subcarpeta llamada `.streamlit`
   y dentro un archivo llamado `secrets.toml` con este contenido exacto
   (reemplazando con tu clave real):
   ```toml
   GROQ_API_KEY = "pega-aqui-tu-clave"
   ```
   Recuerda: si usas el Bloc de notas, guarda el archivo eligiendo
   "Todos los archivos" como tipo, para que no quede como `secrets.toml.txt`.
   Si usas PowerShell, puedes crearlo directo así (más confiable):
   ```powershell
   [System.IO.File]::WriteAllText("$PWD\.streamlit\secrets.toml", 'GROQ_API_KEY = "pega-aqui-tu-clave"')
   ```
5. Vuelve a ejecutar `streamlit run app.py`. Ve a la pestaña "💬 Chatbot",
   escribe una pregunta como *"¿Por qué fui asignado a este grupo?"* y
   debería responderte.

## Paso 3: Publicarlo (para el link que pide tu profesora)

1. Sube toda la carpeta a un repositorio de GitHub (puede ser público o privado).
2. Ve a https://share.streamlit.io e inicia sesión con GitHub.
3. Click en "New app", selecciona tu repositorio y el archivo `app.py`.
4. En "Advanced settings" → "Secrets", pega el mismo contenido de tu
   `secrets.toml` (así no subes tu API key a GitHub).
5. Click en "Deploy". En un par de minutos tendrás tu link público
   (ej: `https://smartcarpool-ulima.streamlit.app`).

## Qué llevar a tu informe / anexos

- Capturas de las 3 pestañas de la app (Registrarme, Resultados, Chatbot).
- El link de Streamlit una vez publicado.
- El link de tu repositorio GitHub.
- Los gráficos de la pestaña "Resultados del clustering" (silhouette score,
  distribución por cluster, mapa) — ya están listos para exportar como imagen.

## Nota sobre el dataset

Usé tu `Ride_Sharing_Dataset.xlsx` como base para el clustering (tomamos
150 registros al azar, usando latitud, longitud y hora como si fueran
estudiantes). Si tu profesora prefiere que reemplaces esto por datos reales
de la Universidad de Lima (150-300 estudiantes), solo tendrías que crear un
Excel con las mismas columnas: `Request Time`, `Latitude Pickup`,
`Longitude Pickup` — el código no necesita cambios, solo reemplazas el archivo
en `data/`.
