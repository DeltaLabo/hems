# mock_streamlit_1.py
# ---------------------------------------------------------
# Dashboard básico para consumir el mock server (FastAPI)
# y visualizar última medición + histórico.
#
# Ejecuta: streamlit run mock_streamlit_1.py
# ---------------------------------------------------------
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Mock Thermal Dashboard", layout="wide")

# ---------- Barra lateral: opciones ----------
st.sidebar.header("Conexión")
base_url = st.sidebar.text_input("Servidor (base URL)", "http://localhost:8000")
user = st.sidebar.text_input("Usuario (profiles/<user>.json|.txt)", "default")
n_points = st.sidebar.number_input("Histórico: últimas N muestras", min_value=1, max_value=10080, value=240, step=60)
refresh = st.sidebar.button("Actualizar")

st.title("📊 Mock Thermal Dashboard")

# ---------- Helpers ----------
def flatten_record(rec: dict) -> dict:
    """
    Aplana un registro: si trae 'indices' anidado, lo expande con prefijo 'idx_'.
    También convierte 'timestamp'/'ts_ms' a una columna datetime 'time'.
    """
    rec = dict(rec)  # copia
    # time
    if "ts_ms" in rec:
        rec["time"] = pd.to_datetime(rec["ts_ms"], unit="ms")
    elif "timestamp" in rec:
        rec["time"] = pd.to_datetime(rec["timestamp"])
    else:
        rec["time"] = pd.Timestamp.utcnow()

    # aplanar indices
    idx = rec.pop("indices", None)
    if isinstance(idx, dict):
        for k, v in idx.items():
            # si viene otro dict (p.ej. perfil_usado), lo ignoramos para graficar
            if isinstance(v, dict):
                # opcional: exponer algunas claves si te interesan
                continue
            rec[f"idx_{k}"] = v
    return rec

def fetch_latest(base: str, user: str) -> dict:
    url = f"{base}/metrics"
    r = requests.get(url, params={"user": user}, timeout=5)
    r.raise_for_status()
    return r.json()

def fetch_last(base: str, n: int, user: str) -> list[dict]:
    url = f"{base}/metrics/last"
    r = requests.get(url, params={"n": n, "user": user}, timeout=10)
    r.raise_for_status()
    return r.json()

# ---------- Llamadas al servidor ----------
try:
    latest_json = fetch_latest(base_url, user)
    hist_json = fetch_last(base_url, n_points, user)

except requests.exceptions.RequestException as e:
    st.error(f"❌ No se pudo conectar al servidor: {e}")
    st.stop()

# ---------- Mostrar última medición ----------
with st.container():
    st.subheader("Última medición")
    latest = flatten_record(latest_json)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Ta (°C) seca", latest.get("dry_bulb_c"))
    col2.metric("Tnw (°C) húmeda", latest.get("wet_bulb_c"))
    col3.metric("Tg (°C) globo", latest.get("globe_temp_c"))
    col4.metric("Va (m/s)", latest.get("air_velocity_ms"))
    col5.metric("RH (%)", latest.get("relative_humidity_pct"))

    # Si existe un índice clave (ej. wbgt efectivo o ISC), muéstralo
    key_idx_candidates = [
        "idx_wbgt_efectivo_c",
        "idx_wbgt_c",
        "idx_isc_pct",
        "idx_dle_alarma_q_min",
    ]
    extra_cols = [k for k in key_idx_candidates if k in latest]
    if extra_cols:
        st.caption("Índices calculados (si disponibles):")
        cols = st.columns(len(extra_cols))
        for c, k in zip(cols, extra_cols):
            c.metric(k.replace("idx_", "").replace("_", " ").upper(), latest.get(k))

# ---------- Histórico ----------
st.subheader("Histórico (últimas N muestras)")
if not hist_json:
    st.info("No hay datos históricos todavía.")
else:
    df = pd.DataFrame([flatten_record(r) for r in hist_json]).sort_values("time")
    df = df.set_index("time")

    # Selección de series a graficar
    default_env_cols = [c for c in ["dry_bulb_c", "wet_bulb_c", "globe_temp_c", "air_velocity_ms"] if c in df.columns]
    default_idx_cols = [c for c in df.columns if c.startswith("idx_")]

    with st.expander("Seleccionar series a graficar (ambientales)", expanded=True):
        env_cols = st.multiselect(
            "Variables ambientales",
            options=default_env_cols,
            default=default_env_cols
        )
        if env_cols:
            st.line_chart(df[env_cols])

    with st.expander("Seleccionar series a graficar (índices calculados)", expanded=False):
        idx_cols = st.multiselect(
            "Índices (prefijo idx_)",
            options=default_idx_cols,
            default=[c for c in default_idx_cols if "wbgt" in c or "isc" in c] or default_idx_cols[:3]
        )
        if idx_cols:
            st.line_chart(df[idx_cols])

    # Tabla y descarga
    with st.expander("Ver tabla de datos"):
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=True).encode("utf-8")
        st.download_button("Descargar CSV", data=csv, file_name="historial_mock.csv", mime="text/csv")

# ---------- Pie ----------
st.caption(
    f"Servidor: {base_url} | Usuario: {user} | "
    f"Última muestra: {latest.get('timestamp', '')}"
)

