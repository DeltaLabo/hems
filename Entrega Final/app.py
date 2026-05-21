import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import hashlib
import requests

# --- Configuración del canal ThingSpeak ---
CHANNEL_ID = 3355700
READ_API_KEY = "SEB48I2QMFR2TOQ3"
URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=500"

# --- Función para cargar datos desde ThingSpeak ---
def cargar_datos_thingspeak():
    response = requests.get(URL)
    data = response.json()["feeds"]
    df = pd.DataFrame(data)
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df

# Configuración de la página
st.set_page_config(page_title="Sistema HEMS", layout="wide")

# Importar csv con datos de metabolismo, cavs y clo
lista_cavs = pd.read_csv("CAVS.csv")
lista_metabolismo = pd.read_csv("Metabolismo.csv")
lista_clo = pd.read_csv("Aislamiento.csv")

# Sistema de autenticación
class AuthenticationSystem:

    def __init__(self, users_file="users.json"):

        self.users_file = Path(users_file)
        self.users = self._load_users()

    def _load_users(self):
        """Cargar usuarios desde el archivo JSON"""
        if self.users_file.exists():

            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_users(self):
        """Guardar usuarios en el archivo JSON"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)

    def hash_password(self, password):
        """Hashear la contraseña usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        """Registrar un nuevo usuario"""
        if username in self.users:
            return False, "El usuario ya existe"

        self.users[username] = {
            "password_hash": self.hash_password(password),

            "created_at": datetime.now().isoformat()
        }

        self._save_users()
        return True, "Usuario registrado exitosamente"

    def verify_user(self, username, password):
        """Verificar credenciales de usuario"""
        if username not in self.users:
            return False, "Usuario no encontrado"
        if self.users[username]["password_hash"] == self.hash_password(
                password):
            return True, "Credenciales válidas"
        return False, "Contraseña incorrecta"

# Inicializar el sistema de autenticación
auth_system = AuthenticationSystem()

# Sidebar con autenticación
with st.sidebar:

    st.title("🔐 Autenticación")
    if 'authenticated' not in st.session_state:

        st.session_state.authenticated = False

    if 'current_user' not in st.session_state:

        st.session_state.current_user = None

    # Si no está autenticado, mostrar formularios de login/registro
    if not st.session_state.authenticated:

        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        with tab1:

            st.subheader("Iniciar Sesión")
            login_user = st.text_input("Usuario", key="login_user")
            login_password = st.text_input(
                "Contraseña", type="password", key="login_password")
            if st.button("Ingresar", key="login_btn"):
                
                if login_user and login_password:
                    success, message = auth_system.verify_user(
                        login_user, login_password)

                    if success:
                        
                        st.session_state.authenticated = True
                        st.session_state.current_user = login_user
                        st.success(f"Bienvenido {login_user}!")
                        st.rerun()
                        
                    else:
                        st.error(message)
                else:
                    st.warning("Por favor complete todos los campos")

        with tab2:

            st.subheader("Crear Cuenta")
            reg_user = st.text_input("Nuevo Usuario", key="reg_user")
            reg_password = st.text_input(
                "Nueva Contraseña",
                type="password",
                key="reg_password")

            reg_confirm = st.text_input(
                "Confirmar Contraseña",
                type="password",
                key="reg_confirm")

            if st.button("Registrar", key="reg_btn"):

                if reg_user and reg_password and reg_confirm:

                    if reg_password != reg_confirm:
                        st.error("Las contraseñas no coinciden")

                    elif len(reg_password) < 4:
                        st.warning(
                            "La contraseña debe tener al menos 4 caracteres")
                    else:

                        success, message = auth_system.register_user(
                            reg_user, reg_password)

                        if success:
                            st.success(message)
                            # Auto-login después del registro
                            st.session_state.authenticated = True
                            st.session_state.current_user = reg_user
                            st.rerun()

                        else:
                            st.error(message)
                else:
                    st.warning("Por favor complete todos los campos")
    else:
        # Usuario autenticado - mostrar información y opción de logout
        st.success(f"✅ Conectado como: **{st.session_state.current_user}**")

        if st.button("Cerrar Sesión"):

            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()
            
# Contenido principal solo para usuarios autenticados
if st.session_state.authenticated:

    st.title("Sistema de Monitoreo de Estrés Térmico")
    st.write(f"Bienvenido **{st.session_state.current_user}** al sistema HEMS")

    # Crear pestañas
    tab1, tab2 = st.tabs(["Evaluación de Tarea", "Monitoreo ThingSpeak"])

    with tab1:
        st.write(
            "Por favor complete la información solicitada a continuación para comenzar la evaluación")

        # Definición del identificador de la tarea para el dashboard
        st.write("## Identificador de la tarea")
        st.write("Por favor ingrese un identificador único para la tarea que se está evaluando, esto es necesario para el correcto funcionamiento del dashboard")
        identificador = st.selectbox(
            "Identificador de la tarea",
            [
                "Seleccione una opción",
                "Corta de caña quemada",
                "Corta de caña verde",
                "Preparación del terreno",
                "Siembra",
                "Control de malezas y limpieza",
                "Carga y acarreo"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Definición de variables necesarias
        st.write("## Datos de entrada")

        # Caracteristicas de la tarea
        st.write("### Caracteristicas de la tarea")
        col3, col4 = st.columns(2)
        with col3:
            postura = st.selectbox(
                "Selecciona una postura de trabajo", [
                    "Seleccione una opción", "De pie", "Sentado", "Agachado"])
            aclimatacion = st.selectbox(
                "¿Los trabajadores están aclimatados?", [
                    "Seleccione una opción", "Si", "No"])
            conveccion = st.selectbox(
                "¿Que tipo de ventilación tiene el área de trabajo?", [
                    "Seleccione una opción", "Natural", "Forzada"])
        with col4:
            radiacion_solar = st.selectbox(
                "¿Estan expuestos al sol?", [
                    "Seleccione una opción", "Si", "No"])
            capucha = st.selectbox(
                "¿Los trabajadores usan capucha?", [
                    "Seleccione una opción", "No", "Si"])

        st.write("### Aislamiento térmico de la ropa")

        st.write("En esta sección se solicitará que ingrese información sobre la vestimenta de los trabajadores, se solicita dos veces para determinar el valor de CAVS y el factor clo")
        # Determinación de Cavs
        st.write("Acontinuación se le presentarán una serie de conjuntos para determinar el valor de CAVS, esto es necesario para calcular el TGBH")
        conjuntos_cavs = lista_cavs.iloc[:, 0].tolist()
        seleccion_cavs = st.selectbox(
            "Seleccione el conjunto que utilizan los trabajadores:",
            conjuntos_cavs)
        cavs = lista_cavs[lista_cavs["Conjunto"]
                          == seleccion_cavs]["CAV"].iloc[0]
        if capucha == "Si":
            cavs += 1
        st.write("El valor de Cavs corresponde a:", cavs)

        # Selección de la vestimenta para el factor clo
        st.write("A continuación se le presentarán una serie de conjuntos de ropa para determinar el valor de clo, esto es necesario para calcular el ISC y SWreq")
        conjuntos_clo = lista_clo.iloc[:, 0].tolist()
        seleccion_clo = st.selectbox(
            "Seleccione el conjunto que utilizan los trabajadores:",
            conjuntos_clo,
            index=0)
        iclo = lista_clo[lista_clo["Ropa de trabajo"]
                         == seleccion_clo]["m²·K/W"].iloc[0]

        # Determinación de la tasa metábolica
        st.write("### Tasa metabólica")

        st.write(
            "Ahora es necesario indicar el metabolismo. Seleccione una tasa metábolica que se ajuste a la labor.")

        st.dataframe(lista_metabolismo)
        tasas = lista_metabolismo.iloc[:, 1].tolist()
        carga_metabolica = st.number_input(
            "Tasa metabólica W",
            min_value=100.0,
            max_value=520.0,
            value=100.0,
            step=10.0)

        # Caracteristicas de los trabajadores
        st.write("### Caracteristicas de los trabajadores")
        # Valores estandarizados para todos los trabajadores
        peso = 85.0  # Estándar fijo solicitado
        altura = 175.0  # Estándar fijo solicitado
        st.info("Se usan valores estándar: 85 kg de peso y 175 cm de altura.")

        # Código comentado para selección manual de peso y estatura (posible uso futuro)
        # col1, col2 = st.columns(2)
        # with col1:
        #     peso = st.number_input(
        #         "Peso (kg)",
        #         min_value=30.0,
        #         max_value=200.0,
        #         value=85.0,
        #         step=0.1)
        #
        # with col2:
        #     altura = st.number_input(
        #         "Altura (cm)",
        #         min_value=100.0,
        #         max_value=250.0,
        #         value=175.0,
        #         step=0.1)

        # Guardar la tarea
        st.title("Guardar la tarea")

        st.write("Finalmente, es necesario guardar la tarea para que pueda ser utilizada en el dashboard, porfavor oprima el botón guardar tarea")

        # Crear el payload con información del usuario
        payload = {
            "usuario": st.session_state.current_user,
            "identificador_tarea": identificador,
            "postura": postura,
            "aclimatación": aclimatacion,
            "convección": conveccion,
            "radiación": radiacion_solar,
            "cavs": int(cavs),
            "carga_metabolica": float(carga_metabolica),
            "peso": float(peso),
            "altura": float(altura),
            "iclo": float(iclo),
            "fecha_creacion": timestamp
        }

        # Declarar la ruta para guardar los archivos
        ruta_base = Path("C:/Repositorios/hems/Esteban/profiles")

        # Crear directorio de usuario si no existe
        user_dir = ruta_base / st.session_state.current_user
        user_dir.mkdir(parents=True, exist_ok=True)

        # Nombre del archivo
        if identificador:
            nombre_archivo = f"{identificador}.json"
            destino = user_dir / nombre_archivo
        else:
            st.warning(
                "Por favor ingrese un identificador de tarea antes de guardar")
            destino = None

        # Verificar que todas las opciones estén seleccionadas
        all_selected = (
            identificador != "Seleccione una opción" and
            postura != "Seleccione una opción" and
            aclimatacion != "Seleccione una opción" and
            conveccion != "Seleccione una opción" and
            radiacion_solar != "Seleccione una opción" and
            capucha != "Seleccione una opción" and
            peso != 30.0 and
            altura != 100.0 and
            carga_metabolica != 100.0
        )

        if st.button(
            "💾 Guardar tarea",
                disabled=not all_selected) and all_selected:
            try:
                # Guardar en archivo JSON
                with open(destino, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

                st.success("Datos guardados exitosamente")

                # Mostrar resumen de los datos guardados
                st.write("### Resumen de datos guardados:")
                st.json(payload)

            except Exception as e:
                st.error(f"No se pudo guardar: {str(e)}")

        if not all_selected:
            st.warning(
                "Por favor seleccione todas las opciones antes de guardar.")

    with tab2:
        if st.button("Cargar desde Base de Datos"):
            df = cargar_datos_thingspeak()
            st.success("Datos cargados correctamente")

            def parsear_field7(valor):
                try:
                    partes = str(valor).split(",")
                    valores = [float(p.strip()) for p in partes]
                    while len(valores) < 11:
                        valores.append(None)
                    return valores[:11]
                except Exception:
                    return [None] * 11

            FIELD7_COLS = [
                "temp_seca", "humedad_relativa", "temp_globo",
                "uv_a", "uv_b", "uv_c",
                "presion_atm", "voltaje", "corriente", "potencia", "energia"
            ]

            parsed = df["field7"].apply(parsear_field7)
            df_p = pd.DataFrame(parsed.tolist(), columns=FIELD7_COLS)
            df_p["created_at"] = pd.to_datetime(df["created_at"])

            st.session_state["df_p"]           = df_p
            st.session_state["datos_cargados"] = True
            st.session_state["fecha_min"]      = df_p["created_at"].min().date()
            st.session_state["fecha_max"]      = df_p["created_at"].max().date()

            if "fecha_inicio" not in st.session_state:
                st.session_state["fecha_inicio"] = df_p["created_at"].min().date()
            if "fecha_fin" not in st.session_state:
                st.session_state["fecha_fin"] = df_p["created_at"].max().date()

        if st.session_state.get("datos_cargados", False):
            df_p      = st.session_state["df_p"]
            fecha_min = st.session_state["fecha_min"]
            fecha_max = st.session_state["fecha_max"]

            FIELD7_LABELS = {
                "temp_seca":        ("🌡️ Temperatura Seca",     "°C"),
                "humedad_relativa": ("💧 Humedad Relativa",     "%"),
                "temp_globo":       ("🔆 Temperatura de Globo", "°C"),
                "uv_a":             ("☀️ UV-A",                 "W/m²"),
                "uv_b":             ("☀️ UV-B",                 "W/m²"),
                "uv_c":             ("☀️ UV-C",                 "W/m²"),
                "presion_atm":      ("🌬️ Presión Atmosférica",  "hPa"),
                "voltaje":          ("⚡ Voltaje",              "V"),
                "corriente":        ("⚡ Corriente",            "A"),
                "potencia":         ("💡 Potencia",             "W"),
                "energia":          ("🔋 Energía",              "kWh"),
            }
            FIELD7_COLS = list(FIELD7_LABELS.keys())

            # --- Valores Actuales ---
            st.subheader("📊 Valores Actuales")
            ultimo = df_p.iloc[-1]
            cols_grid = st.columns(4)
            for i, (key, (label, unidad)) in enumerate(FIELD7_LABELS.items()):
                val = ultimo[key]
                display = f"{val:.2f} {unidad}" if val is not None else "N/D"
                cols_grid[i % 4].metric(label, display)

            # --- Filtro de fechas ---
            st.subheader("📅 Historial")
            col_f1, col_f2 = st.columns(2)

            col_f1.date_input(
                "Fecha inicio",
                min_value=fecha_min,
                max_value=fecha_max,
                key="fecha_inicio"
            )
            col_f2.date_input(
                "Fecha fin",
                min_value=fecha_min,
                max_value=fecha_max,
                key="fecha_fin"
            )

            mascara = (
                (df_p["created_at"].dt.date >= st.session_state["fecha_inicio"]) &
                (df_p["created_at"].dt.date <= st.session_state["fecha_fin"])
            )
            df_filtrado = df_p[mascara].set_index("created_at")

            if df_filtrado.empty:
                st.warning(f"⚠️ No hay datos entre {st.session_state['fecha_inicio'].strftime('%d/%m/%Y')} y {st.session_state['fecha_fin'].strftime('%d/%m/%Y')}.")
            else:
                # ✅ Solo tabla, sin multiselect ni gráficas
                df_tabla = df_filtrado[FIELD7_COLS].copy()
                df_tabla.columns = [
                    f"{FIELD7_LABELS[k][0]} ({FIELD7_LABELS[k][1]})" for k in FIELD7_COLS
                ]
                df_tabla.index = df_tabla.index.strftime("%d/%m/%Y %H:%M:%S")
                df_tabla.index.name = "Fecha y Hora"

                with st.expander("📋 Ver tabla de datos completa"):
                    st.dataframe(df_tabla, width='stretch')

        else:
            st.warning("Presiona el botón para cargar datos del canal ThingSpeak.")