# mock_streamlit2.py
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
import hashlib
import json
from pathlib import Path

st.set_page_config(page_title="Mock Thermal Dashboard", layout="wide")

# Sistema de autenticación
class AuthenticationSystem:
    def __init__(self, users_file="users.json"):
        self.users_file = Path(users_file)
        self.users = self._load_users()
    
    def _load_users(self):
        """Cargar usuarios desde el archivo JSON"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Error cargando usuarios: {e}")
                return {}
        return {}
    
    def hash_password(self, password):
        """Hashear la contraseña usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, username, password):
        """Verificar credenciales de usuario"""
        if username not in self.users:
            return False, "Usuario no encontrado"
        
        if self.users[username]["password_hash"] == self.hash_password(password):
            return True, "Credenciales válidas"
        return False, "Contraseña incorrecta"

# Inicializar el sistema de autenticación
auth_system = AuthenticationSystem()

# ---------- Autenticación en Sidebar ----------
st.sidebar.header("🔐 Autenticación")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Si no está autenticado, mostrar formulario de login
if not st.session_state.authenticated:
    st.sidebar.subheader("Iniciar Sesión")
    login_user = st.sidebar.text_input("Usuario")
    login_password = st.sidebar.text_input("Contraseña", type="password")
    
    if st.sidebar.button("Ingresar al Dashboard"):
        if login_user and login_password:
            success, message = auth_system.verify_user(login_user, login_password)
            if success:
                st.session_state.authenticated = True
                st.session_state.current_user = login_user
                st.sidebar.success(f"Bienvenido {login_user}!")
                st.rerun()
            else:
                st.sidebar.error(message)
        else:
            st.sidebar.warning("Por favor complete todos los campos")
    
    # Información adicional
    st.sidebar.info("""
    **Credenciales requeridas:**
    - Use el mismo usuario y contraseña de la app de ingreso de datos
    - Si no tiene una cuenta, créela en la app de ingreso de datos primero
    """)
    
    # No mostrar el contenido principal si no está autenticado
    st.title("📊 Mock Thermal Dashboard")
    st.warning("🔒 Por favor inicie sesión en el sidebar para acceder al dashboard")
    st.stop()

else:
    # Usuario autenticado - mostrar información y opción de logout
    st.sidebar.success(f"✅ Conectado como: **{st.session_state.current_user}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

# ---------- Barra lateral: opciones (solo para autenticados) ----------
st.sidebar.header("Configuración de Conexión")
base_url = st.sidebar.text_input("Servidor (base URL)", "http://localhost:8000")
# El usuario ahora viene de la autenticación, no del input
user = st.session_state.current_user
n_points = st.sidebar.number_input("Histórico: últimas N muestras", min_value=1, max_value=10080, value=240, step=60)
refresh = st.sidebar.button("Actualizar Datos")

st.sidebar.header("Información")
st.sidebar.info(f"""
**Usuario activo:** {user}
**Perfil cargado:** profiles/{user}/
**Servidor:** {base_url}
""")

st.title("📊 Mock Thermal Dashboard")
st.write(f"**Usuario:** {user} | **Servidor:** {base_url}")

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
    st.error(f"Verifique que el servidor en {base_url} esté ejecutándose")
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
        st.download_button("Descargar CSV", data=csv, file_name=f"historial_{user}.csv", mime="text/csv")

# ---------- Información del perfil ----------
try:
    # Intentar cargar información del perfil del usuario
    profile_path = Path(f"profiles/{user}")
    if profile_path.exists():
        st.sidebar.subheader("Tareas del usuario")
        task_files = list(profile_path.glob("*.json"))
        if task_files:
            st.sidebar.write(f"**Tareas encontradas:** {len(task_files)}")
            for task_file in task_files[-5:]:  # Mostrar las 5 más recientes
                st.sidebar.write(f"• {task_file.stem}")
        else:
            st.sidebar.write("No se encontraron tareas")
except Exception as e:
    st.sidebar.warning("No se pudieron cargar las tareas del usuario")

# ---------- Pie ----------
st.caption(
    f"Servidor: {base_url} | Usuario: {user} | "
    f"Última muestra: {latest.get('timestamp', '')} | "
    f"Actualizado: {datetime.now().strftime('%H:%M:%S')}"
)