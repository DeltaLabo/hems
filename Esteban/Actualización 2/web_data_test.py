import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(layout="wide")
st.title("🔥 Mapa de Calor - Monitoreo Ambiental")

# --- 1. Datos de la API del NWS (EE.UU.) ---
@st.cache_data
def get_stations_data(state="CA"):
    """Obtiene estaciones meteorológicas de un estado en EE.UU."""
    url = f"https://api.weather.gov/stations?state={state}"
    response = requests.get(url, headers={"User-Agent": "MyStreamlitApp"})
    return response.json()

@st.cache_data
def get_observations(station_id):
    """Obtiene datos actuales de una estación."""
    url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
    response = requests.get(url, headers={"User-Agent": "MyStreamlitApp"})
    return response.json()

# --- Interfaz de usuario ---
st.sidebar.header("Filtros")
state = st.sidebar.selectbox("Estado (EE.UU.)", ["CA", "TX", "FL", "PR"])
stations_data = get_stations_data(state)

if stations_data and "features" in stations_data:
    # Crear DataFrame con estaciones y temperaturas
    stations_list = []
    for station in stations_data["features"]:
        station_id = station["properties"]["stationIdentifier"]
        obs = get_observations(station_id)
        if obs and "properties" in obs:
            temp = obs["properties"].get("temperature", {}).get("value")
            if temp:
                stations_list.append({
                    "Estación": station["properties"]["name"],
                    "Latitud": station["geometry"]["coordinates"][1],
                    "Longitud": station["geometry"]["coordinates"][0],
                    "Temperatura (°C)": temp,
                })
    
    df = pd.DataFrame(stations_list)
    
    # --- 2. Mapa de Calor con Folium ---
    st.subheader("🗺️ Mapa de Calor de Temperaturas")
    m = folium.Map(location=[37.0, -120.0], zoom_start=6)  # Centro de California
    
    # Capa de HeatMap (requiere datos: [lat, lon, intensity])
    heat_data = [[row["Latitud"], row["Longitud"], row["Temperatura (°C)"]] for _, row in df.iterrows()]
    HeatMap(heat_data, name="Temperatura").add_to(m)
    
    # Marcadores individuales
    for _, row in df.iterrows():
        folium.Marker(
            [row["Latitud"], row["Longitud"]],
            popup=f"{row['Estación']}: {row['Temperatura (°C)']}°C",
            tooltip="Ver detalles"
        ).add_to(m)
    
    folium_static(m, width=1000)
    
    # --- 3. Gráfico de Barras con Plotly ---
    st.subheader("📊 Temperaturas por Estación")
    fig = px.bar(df, x="Estación", y="Temperatura (°C)", color="Temperatura (°C)")
    st.plotly_chart(fig)
    
    # --- 4. Tabla de Datos ---
    st.subheader("📝 Datos Crudos")
    st.dataframe(df)
    
else:
    st.warning("No se encontraron estaciones en el estado seleccionado.")

# --- Nota sobre Costa Rica ---
st.sidebar.warning("""
**⚠️ Limitación**: La API del NWS solo cubre EE.UU.  
**Para Costa Rica**, usa:  
- OpenWeatherMap (con API key).  
- Datos del IMN (web scraping).  
""")