import streamlit as st
import pandas as pd
import requests
import datetime

# --- Configuración del canal ---
CHANNEL_ID = 3355700
READ_API_KEY = "SEB48I2QMFR2TOQ3"
URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=500"
# URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/fields/2.json?api_key={READ_API_KEY}&results=100"

# --- Cargar datos desde ThingSpeak ---
def cargar_datos():
    response = requests.get(URL)
    data = response.json()["feeds"]
    df = pd.DataFrame(data)
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df

# --- Interfaz Streamlit ---
st.title("Monitoreo Ambiental y Estrés Térmico")

if st.button("Cargar desde Base de Datos"):
    df = cargar_datos()
    st.write(df.columns)
    st.success("Datos cargados correctamente")
    print(df)

    # --- Valores actuales ---
    ultimo = df.iloc[-1]
    st.subheader("Valores Actuales")
    col1, col2 = st.columns(2)
    col1.metric("Índice de Estrés Térmico", ultimo["field3"], "Riesgo Alto")
    col2.metric("Temperatura (°C)", ultimo["field4"])
    st.metric("Humedad (%)", ultimo["field3"])

    # --- Gráficas históricas ---
    st.subheader("Historial de Índices de Estrés Térmico")
    st.line_chart(df[["created_at", "field1"]].set_index("created_at"))

    st.subheader("Historial de Variables Ambientales")
    st.line_chart(df[["created_at", "field2", "field3"]].set_index("created_at"))

    # --- Configuración de límites ---
    st.subheader("Configuración de Límites de Estrés Térmico")
    lim_moderado = st.slider("Límite Moderado", 60.0, 80.0, 72.0)
    lim_alto = st.slider("Límite Alto", 70.0, 90.0, 78.0)
    lim_peligro = st.slider("Límite Peligro", 75.0, 100.0, 82.0)
    if st.button("Guardar Configuración"):
        st.info("Configuración guardada (simulada).")

else:
    st.warning("Presiona el botón para cargar datos del canal ThingSpeak.")
