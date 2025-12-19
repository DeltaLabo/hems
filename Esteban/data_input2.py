import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import hashlib
import os

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
        
        if self.users[username]["password_hash"] == self.hash_password(password):
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
            login_password = st.text_input("Contraseña", type="password", key="login_password")
            
            if st.button("Ingresar", key="login_btn"):
                if login_user and login_password:
                    success, message = auth_system.verify_user(login_user, login_password)
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
            reg_password = st.text_input("Nueva Contraseña", type="password", key="reg_password")
            reg_confirm = st.text_input("Confirmar Contraseña", type="password", key="reg_confirm")
            
            if st.button("Registrar", key="reg_btn"):
                if reg_user and reg_password and reg_confirm:
                    if reg_password != reg_confirm:
                        st.error("Las contraseñas no coinciden")
                    elif len(reg_password) < 4:
                        st.warning("La contraseña debe tener al menos 4 caracteres")
                    else:
                        success, message = auth_system.register_user(reg_user, reg_password)
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
    st.write(f"Bienvenido **{st.session_state.current_user}** al sistema CALA, por favor complete la información solicitada a continuación para comenzar la evaluación")

    # Definición del identificador de la tarea para el dashboard
    st.write("## Identificador de la tarea")
    st.write("Por favor ingrese un identificador único para la tarea que se está evaluando, esto es necesario para el correcto funcionamiento del dashboard")
    st.write("Coloque el nombre de su empresa seguido de un guión y una breve descripción de la tarea, por ejemplo: EmpresaX-TareaY")
    identificador = st.text_input("Identificador de la tarea")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Definición de variables necesarias
    st.write("## Datos de entrada")

    # Caracteristicas de la tarea
    st.write("### Caracteristicas de la tarea")
    col3, col4 = st.columns(2)
    with col3:
        postura = st.selectbox("Selecciona una postura de trabajo", ["De pie", "Sentado", "Agachado"])
        aclimatacion = st.selectbox("¿Los trabajadores están aclimatados?", ["Si", "No"])
        conveccion = st.selectbox("¿Que tipo de ventilación tiene el área de trabajo?", ["Natural", "Forzada"])
    with col4:
        radiacion_solar = st.selectbox("¿Estan expuestos al sol?", ["Si", "No"])
        capucha = st.selectbox("¿Los trabajadores usan capucha?", ["No", "Si"])
        
    st.write("### Aislamiento térmico de la ropa")

    st.write("En esta sección se solicitará que ingrese información sobre la vestimenta de los trabajadores, se solicita dos veces para determinar el valor de CAVS y el factor clo")
    # Determinación de Cavs
    st.write("Acontinuación se le presentarán una serie de conjuntos para determinar el valor de CAVS, esto es necesario para calcular el TGBH")
    conjuntos_cavs = lista_cavs.iloc[:, 0].tolist()
    seleccion_cavs = st.selectbox("Seleccione el conjunto que utilizan los trabajadores:", conjuntos_cavs)
    cavs = lista_cavs[lista_cavs["Conjunto"] == seleccion_cavs]["CAV"].iloc[0]
    if capucha == "Si": 
        cavs += 1
    st.write("El valor de Cavs corresponde a:", cavs)

    # Selección de la vestimenta para el factor clo
    st.write("A continuación se le presentarán una serie de conjuntos de ropa para determinar el valor de clo, esto es necesario para calcular el ISC y SWreq")
    conjuntos_clo = lista_clo.iloc[:, 0].tolist()
    seleccion_clo = st.selectbox("Seleccione el conjunto que utilizan los trabajadores:", conjuntos_clo)
    iclo = lista_clo[lista_clo["Ropa de trabajo"] == seleccion_clo]["m²·K/W"].iloc[0]
        
    # Determinación de la tasa metábolica
    st.write("### Tasa metabólica")

    st.write("Ahora es necesario indicar el metabolismo. Seleccione una tasa metábolica que se ajuste a la labor.")

    st.dataframe(lista_metabolismo)
    tasas = lista_metabolismo.iloc[:, 1].tolist()
    carga_metabolica = st.number_input("Tasa metabólica W", min_value=100.0, max_value=520.0, value=160.0, step=10.0)

    # Caracteristicas de los trabajadores
    st.write("### Caracteristicas de los trabajadores")
    st.write("A continuación, es necesario ingresar las características de los trabajadores que realizarán la tarea.")
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)
        
    with col2:
        altura = st.number_input("Altura (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.1)

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
        st.warning("Por favor ingrese un identificador de tarea antes de guardar")
        destino = None

    if st.button("💾 Guardar JSON") and destino:
        try:
            with destino.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            st.success(f"Archivo guardado en: {destino}")
            st.code(str(destino))
            
            # Mostrar resumen de los datos guardados
            st.write("### Resumen de datos guardados:")
            st.json(payload)
            
        except Exception as e:
            st.error(f"No se pudo guardar el archivo: {e}")

else:
    # Mensaje cuando no está autenticado
    st.title("Sistema de Monitoreo de Estrés Térmico")
    st.warning("🔒 Por favor inicie sesión o regístrese en el sidebar para acceder al sistema")
    st.info("""
    **Instrucciones:**
    1. Use el sidebar para iniciar sesión o crear una cuenta nueva
    2. Una vez autenticado, podrá ingresar los datos de la tarea
    3. Los datos se guardarán asociados a su usuario
    """)