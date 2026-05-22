import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import hashlib
import requests
import matplotlib.pyplot as plt
import altair as alt
import math

# --- Configuración del canal ThingSpeak ---
CHANNEL_ID = 3355700
READ_API_KEY = "SEB48I2QMFR2TOQ3"
URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=500"

# Importar la función desde el archivo funciones.py
from funcionesfang import fanger, indice_de_sudoracion, tgbh, indice_sobrecarga_calorica, format_time, indice_de_calor

#Importar csv con datos de metabolismo, cavs y clo
lista_cavs = pd.read_csv("data/CAVS.csv")
lista_metabolismo = pd.read_csv("data/Metabolismo.csv")
lista_clo = pd.read_csv("data/Aislamiento.csv")
lista_clofanger= pd.read_csv("data/AislamientoFanger.csv")  

# --- Función para cargar datos desde ThingSpeak ---
def cargar_datos_thingspeak():
    response = requests.get(URL)
    data = response.json()["feeds"]
    df = pd.DataFrame(data)
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df

# Configuración de la página
st.set_page_config(page_title="Sistema HEMS", layout="wide")

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
        # Título principal
        st.title("🔥 Sistema HEMS - Evaluación de Estrés Térmico")
        st.markdown("---")

        # Mensaje de bienvenida
        st.header("🌡️ Bienvenido al Sistema HEMS")
        st.write("""
        Complete la información solicitada a continuación para comenzar la evaluación de estrés térmico 
        en el ambiente laboral.  
        Deslice hacia abajo para navegar el sistema. 
        Este sistema le permitirá analizar las condiciones térmicas y obtener recomendaciones para proteger la salud de los trabajadores.
        """)

        # Información sobre normas con expander
        with st.expander("📚 **Normativas y Métodos de Evaluación Utilizados**", expanded=False):
            st.write("""
            Este sistema está basado en las siguientes normativas nacionales e internacionales:
            
            **Normativas Nacionales:**
            - **Reglamento para la prevención y protección de las personas trabajadoras expuestas a estrés térmico por calor**
        
            **Normativas Internacionales:**
            - **ISO 7243:** Ambientes térmicos calurosos - Estimación del estrés térmico del trabajador
            - **ISO 8996:** Ergonomía del ambiente térmico - Determinación de la tasa metabólica
            -**ISO 9920:** Ergonomía del ambiente térmico - Estimación de la resistencia térmica y la capacidad de evaporación de la ropa
            - **NTP 18 (ISC):** Evaluación de la exposición al calor
            - **NTP 323:** Estrés térmico: Índice de sobrecarga térmica
            - **UNE-EN ISO 7730:** Ergonomía del ambiente térmico:Determinación analítica e interpretación del bienestar térmico mediante el cálculo de los índices PMV y PPD y los criterios de bienestar térmico local 
            
            **Métodos de Evaluación Implementados:**
            - **Índice de Calor (Heat Index):** Evalúa la percepción del calor considerando temperatura y humedad
            - **TGBH (Temperatura de Globo y Bulbo Húmedo):** Temperatura de globo y bulbo húmedo para estrés térmico
            - **SWreq (Índice de Sudoración Requerida):** Calcula la sudoración necesaria para el equilibrio térmico y tiempos límite de exposición
            - **ISC (Índice de Sobrecarga Calórica):** Evalúa la carga calórica acumulada en el cuerpo
            - **Índice de Calor (Heat Index):** Evalúa la percepción del calor considerando temperatura y humedad
            - **Fanger (PMV y PPD):** Evaluación del confort térmico basada en la temperatura, humedad, velocidad del aire, radiación y aislamiento de la ropa
                    
            """)

        # Información sobre el prototipo
        st.info("""
        **⚠️ Importante: Esta es una versión prototipo**

        Esta herramienta se encuentra en fase de desarrollo y estamos validando su funcionamiento. 
        Agradecemos cualquier comentario o sugerencia que pueda tener para mejorar la aplicación.
        """)

        st.warning("""
        **🎯 Objetivo de esta prueba:**

        El objetivo principal de esta primera versión es evaluar:
        - Los métodos de ingreso de datos
        - La visualización de resultados  
        - La experiencia de usuario general

        **Nota:** Los cálculos realizados son aproximados y no deben ser utilizados para la 
        toma de decisiones críticas en esta etapa de desarrollo.
        """)

        st.markdown("---")
        st.subheader("Comience completando los datos a continuación 👇")

        #Definición de variables necesarias
        st.write("## 📥 Datos de entrada")
        st.write("### 🌍 Variables ambientales")

        if not st.session_state.get("datos_cargados", False):
            st.warning("⚠️ No hay datos cargados. Ve a la pestaña **Monitoreo ThingSpeak** y presiona 'Cargar desde Base de Datos'.")
        else:
            temp_aire        = st.session_state["ts_temp_aire"]
            temp_globo       = st.session_state["ts_temp_globo"]
            humedad_relativa = st.session_state["ts_humedad_relativa"]
            temp_bulbo       = 28.00   # valor fijo si el sensor no lo mide
            velocidad_aire   = 0.016   # valor fijo si el sensor no lo mide

            st.info("📡 Datos cargados desde ThingSpeak (promedio del historial)")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Temperatura seca (°C)", f"{temp_aire:.2f}")
                st.metric("Temperatura de globo (°C)", f"{temp_globo:.2f}")
                st.metric("Humedad relativa (%)", f"{humedad_relativa:.2f}")
            with col2:
                st.metric("Temperatura de bulbo húmedo (°C)", f"{temp_bulbo:.2f}")
                st.metric("Velocidad del aire (m/s)", f"{velocidad_aire:.3f}")            
                
            #Caracteristicas de la tarea
            st.write("### 💼 Caracteristicas de la tarea")
            st.write("Indique los siguientes aspectos relacionados a las caracteristicas de la tarea")
            col3,col4=st.columns(2)
            with col3:
                postura = st.selectbox("Selecciona una postura de trabajo", ["De pie", "Sentado", "Agachado"])
                aclimatacion = st.selectbox("¿Los trabajadores están aclimatados?", ["Si", "No"])
                conveccion = st.selectbox("¿Que tipo de ventilación tiene el área de trabajo?", ["Natural", "Forzada"])
            with col4:
                radiacion_solar = st.selectbox("¿Estan expuestos al sol?", ["Si", "No"])
                capucha = st.selectbox("¿Los trabajadores usan capucha?", ["No", "Si"])
                
                
            st.write("### 👕 Aislamiento térmico de la ropa")

            #Determinación de Cavs
            st.write("Acontinuación se le presentarán una serie de conjuntos para determinar el valor de CAVS, esto es necesario para calcular el TGBH")
            st.write("Los CAVS son un valor en grados Celsius estudiados para ciertos conjuntos predeterminados, según que conjunto se use se le suma este valor al calculo del tgbh")
            conjuntos_cavs= lista_cavs.iloc[:,0].tolist()
            seleccion_cavs= st.selectbox("Seleccione el conjunto que utilizan los trabajadores:",conjuntos_cavs)
            cavs=lista_cavs[lista_cavs["Conjunto"]==seleccion_cavs]["CAV"].iloc[0]
            if capucha == "Si": 
                cavs +=1
            st.write ("El valor de Cavs corresponde a:", cavs)

            #Determinación de la tasa metábolica
            st.write("### 💪 Tasa metabólica")

            st.write("Ahora es necesario indicar el metabolismo. Seleccione una tasa metábolica que se ajuste a la labor.")

            st.dataframe(lista_metabolismo)
            tasas=lista_metabolismo.iloc[:,1].tolist()
            carga_metabolica=st.number_input("Ingrese la tasa metabólica (W/m²)", min_value=100, max_value=600, value=160, step=10)

            # Calcular e imprimir los resultados
            st.write("## 📊 Resultados de Evaluación")
            #Indice de Calor
            #Llamar a la función indice de calor
            st.write("### 📈 Resultados Índice de Calor")

            heat_index,nivel,efecto,medidas_de_salud,nivel_para_medidas=indice_de_calor(temp_aire,humedad_relativa,radiacion_solar)

            #Graficar el indice de calor 

            #Inicio de prueba de gráfico heat index

            # ---------------------------
            # 2) PREPARAR DATOS PARA UNA SOLA BARRA
            # ---------------------------
            max_ref = max(140, math.ceil(heat_index) + 10)

            # Crear DataFrame con UNA sola fila - la del nivel actual
            df_single = pd.DataFrame({
                "Nivel": [nivel],
                "Heat_Index": [heat_index]
            })

            # Mapeo de colores por nivel
            color_mapping = {
                "Nivel I": "#22c55e",  # verde
                "Nivel II": "#eab308",  # amarillo
                "Nivel III": "#f97316", # naranja
                "Nivel IV": "#ef4444"   # rojo
            }

            # ---------------------------
            # 3) GRÁFICO DE UNA SOLA BARRA
            # ---------------------------
            bar = (
                alt.Chart(df_single)
                .mark_bar(size=100)  # Tamaño de la barra
                .encode(
                    x=alt.X("Nivel:N", title="Nivel de Riesgo"),  # Solo muestra el nivel actual
                    y=alt.Y("Heat_Index:Q", title="Índice de calor", 
                            scale=alt.Scale(domain=[0, max_ref])),
                    color=alt.Color("Nivel:N", 
                                scale=alt.Scale(domain=list(color_mapping.keys()), 
                                                range=list(color_mapping.values())), 
                                legend=None),
                    tooltip=[
                        alt.Tooltip("Nivel:N", title="Nivel"),
                        alt.Tooltip("Heat_Index:Q", title="Índice de calor", format=".1f")
                    ]
                )
                .properties(height=400, title="Índice de Calor Actual")
            )

            # Texto encima de la barra con el valor
            text = bar.mark_text(
                align='center',
                baseline='bottom',
                dy=-10,  # Desplazamiento vertical
                color='black',
                fontSize=14,
                fontWeight='bold'
            ).encode(
                text=alt.Text("Heat_Index:Q", format=".1f")
            )

            # Línea de referencia opcional para contexto (puedes quitarla si no la necesitas)
            rule = (
                alt.Chart(pd.DataFrame({"Reference": [heat_index]}))
                .mark_rule(color="gray", strokeDash=[5, 5])
                .encode(y="Reference:Q")
            )

            # Mostrar gráfico
            st.altair_chart(bar + text + rule, use_container_width=True)

            # ---------------------------
            # 4) MÉTRICAS Y EFECTOS (sin cambios - como lo tenías bien)
            # ---------------------------
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Índice de Calor", f"{heat_index:.1f}")
            with col2:
                st.metric("Nivel de Riesgo", nivel)
            with col3:
                st.metric("Humedad Relativa", f"{humedad_relativa:.0f}%")

            st.subheader("🎯 Efectos en la Salud - " + nivel)
            st.info(efecto)

            #Medidas de prevención y protección
            st.subheader("🛡️ Medidas de Prevención y Protección")
            if radiacion_solar == "Si":
                st.write("Según el reglamento nacional, cuando existe exposición al sol se deben tomar las medidas correspondientes al siguiente nivel excepto para el Nivel IV.")
            with st.expander(f"📋 Ver medidas de prevención para {nivel_para_medidas}", expanded=False):
                st.write(f"**Medidas específicas para {nivel_para_medidas}:**")
                
                # Listar todas las medidas de la lista medidas_de_salud
                for i, medida in enumerate(medidas_de_salud, 1):
                    st.write(f"• {medida}")


            # Información adicional (opcional - manteniendo tu estructura original)
            with st.expander("📊 Información sobre los niveles"):
                st.write("""
                **Nivel I (Verde)**: 80 - 90 - Precaución  
                **Nivel II (Amarillo)**: 91 - 103 - Precaución extrema  
                **Nivel III (Naranja)**: 103 - 124 - Peligro  
                **Nivel IV (Rojo)**: 125 + - Peligro extremo  
                """)
                
            #Final de prueba de gráfico heat index

            #TGBH
            #Llamar función tgbh
            st.write("### 🌡️ Resultados TGBH")
            st.write("El TGBH es un índice que considera la temperatura del aire, la humedad, la radiación solar y la velocidad del aire para evaluar el estrés térmico en ambientes calurosos.")
            st.write("Esta diseñado para evaluar jornadas de máximo 8 horas y con mediciones de al menos una hora.")
            wbgt,tgbh_efectivo,tgbh_ref,estado=tgbh(radiacion_solar,temp_aire,temp_globo,temp_bulbo,cavs,carga_metabolica,aclimatacion)
            # Mostrar los valores asignados después de que el usuario presione el botón

            st.write(f"TGBH: {round(wbgt,2)}")
            st.write(f"TGBH efectivo: {round(tgbh_efectivo,2)}")
            st.write(f"TGBH referencia: {round(tgbh_ref,2)}")
            st.write(f"Usted se encuentra en: {estado}")
            # Definir las funciones para las dos curvas
            def curva_aclimatada(x):
                return 56.7 - 11.5 * np.log10(x)

            def curva_no_aclimatada(x):
                return 59.9 - 14.1 * np.log10(x)
            x_values = np.linspace(100, 600, 500)
            y_aclimatada = curva_aclimatada(x_values)
            y_no_aclimatada = curva_no_aclimatada(x_values)
            # Crear el gráfico
            fig_1, ax = plt.subplots(figsize=(8, 6))
            # Graficar las curvas
            ax.plot(x_values, y_aclimatada, label="Personas Aclimatadas", color="blue", linewidth=2)
            ax.plot(x_values, y_no_aclimatada, label="Personas No Aclimatadas", color="red", linestyle='--', linewidth=2)
            # Graficar el punto
            ax.scatter(carga_metabolica, tgbh_efectivo, color="green", zorder=5, label=f'Punto ({carga_metabolica},{round(tgbh_efectivo),2})')
            # Etiquetas y título
            ax.set_xlabel('Carga Metabólica')
            ax.set_ylabel('TGBH Efectivo')
            ax.set_title('Curvas de Aclimatación y No Aclimatación')
            ax.legend()
            # Ajustar límites de los ejes
            ax.set_xlim(100, 600)
            ax.set_ylim(15, 45)

            # Mostrar gráfico
            st.pyplot(fig_1)

            #Compuerta lógica para mostrar métodos de evaluación
            #Si se encuentra en estrés térmico, mostrará el método de evaluación SWreq e ISC, de lo contrario, mostrará Fanger. Fanger aun no se ha agregado.

            if estado == "Estrés Térmico":
                st.write("### Método de evaluación: SWreq e ISC")
                st.write("Ya que el trabajador se encuentra en estrés térmico, se recomienda utilizar el método de evaluación SWreq e ISC")
                #Selección de la vestimenta para el factor clo
                st.write("A continuación se le presentarán una serie de conjuntos de ropa para determinar el valor de clo, esto es necesario para calcular el ISC y SWreq y es diferente al valor CAVS")
                conjuntos_clo= lista_clo.iloc[:,0].tolist()
                seleccion_clo= st.selectbox("Seleccione el conjunto que utilizan los trabajadores:",conjuntos_clo)
                iclo=lista_clo[lista_clo["Ropa de trabajo"]==seleccion_clo]["m²·K/W"].iloc[0]
                st.write("Tambien es necesario indicar la altura y peso promedio de los trabajadores") 
                col5,col6=st.columns(2)  
                with col5:
                    altura=st.number_input("Altura promedio de los trabajadores (cm)", min_value=0.00, max_value=300.00, value=175.00)
                with col6:
                    peso=st.number_input("Peso promedio de los trabajadores (kg)", min_value=50.00, max_value=150.00, value=85.00)
                
                #Nuevas visualizaciones ISC y Swreq    
                
                st.write("### Resultados SWreq")
                # SWreq
                st.write("Por favor tome en cuenta que el índice SWreq no es aplicable a exposiciones menores a 30 minutos o cuando emax < 0")
                mostrar_swreq = st.button("Calcular Índice de sudoración requerida")
                if mostrar_swreq:
                    
                    # Llamar a la función indice de sudoración
                    dle_alarma_q, dle_peligro_q, dle_alarma_d, dle_peligro_d = indice_de_sudoracion(temp_aire, temp_globo, temp_bulbo, iclo, carga_metabolica, velocidad_aire, postura, aclimatacion, conveccion)
                    if dle_alarma_q == 0 and dle_peligro_q == 0 and dle_alarma_d == 0 and dle_peligro_d == 0:
                        st.error("❌ Error en el cálculo de SWreq. Cuando emax < 0 este metodo no puede ser utilizado. Por favor, revise los datos ingresados.")
                    else:
                        st.success("✅ Cálculo de SWreq completado exitosamente.")
                        # VISUALIZACIÓN MEJORADA - DIRECTAMENTE EN EL FLUJO
                        st.success("### 📈 Resultados SWreq - Tiempos Límite")

                        # Tarjetas con métricas en columnas
                        st.write("### 📋 Resumen de Límites")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                label="🟡 Alarma Acumulación",
                                value=format_time(dle_alarma_q) if dle_alarma_q != float('inf') else "Sin límite"
                            )
                        
                        with col2:
                            st.metric(
                                label="🔴 Peligro Acumulación", 
                                value=format_time(dle_peligro_q) if dle_peligro_q != float('inf') else "Sin límite"
                            )
                        
                        with col3:
                            st.metric(
                                label="🟠 Alarma Deshidratación",
                                value=format_time(dle_alarma_d) if dle_alarma_d != float('inf') else "Sin límite"
                            )
                        
                        with col4:
                            st.metric(
                                label="🔴 Peligro Deshidratación",
                                value=format_time(dle_peligro_d) if dle_peligro_d != float('inf') else "Sin límite"
                            )
                        
                        # Opción 3: Alertas visuales si los tiempos son críticos
                        st.write("### 🚨 Alertas de Seguridad")
                        
                        if dle_alarma_q != float('inf') and dle_alarma_q < 120:  # Menos de 2 horas
                            st.warning(f"⚠️ **Alarma por Acumulación de Calor**: Límite en {format_time(dle_alarma_q)} - Monitorear continuamente")
                        
                        if dle_peligro_q != float('inf') and dle_peligro_q < 240:  # Menos de 4 horas  
                            st.error(f"🚨 **Peligro por Acumulación de Calor**: Límite en {format_time(dle_peligro_q)} - Tomar acciones inmediatas")
                        
                        if dle_alarma_d != float('inf') and dle_alarma_d < 120:
                            st.warning(f"💧 **Alarma por Deshidratación**: Límite en {format_time(dle_alarma_d)} - Aumentar hidratación")
                        
                        if dle_peligro_d != float('inf') and dle_peligro_d < 240:
                            st.error(f"🔥 **Peligro por Deshidratación**: Límite en {format_time(dle_peligro_d)} - Hidratación urgente requerida")

            # ISC - CÓDIGO CORREGIDO
                if iclo <0.6 and aclimatacion == "Si":
                    st.write("### Condiciones adecuadas para el cálculo del ISC")
                    st.write("Por favor tome en cuenta que el método ISC es recomendado para exposiciones mayores a 30 minutos y se recomienda utilizarlo en trabajadores jóvenes y sanos")
                    mostrar_isc = st.button("Calcular Índice de Sobrecarga de Calor")
                    if mostrar_isc:
                        # Llamar a la función
                        isc, clasificacion_isc, tiempo_exp_per, emax, ereq = indice_sobrecarga_calorica(
                            carga_metabolica, velocidad_aire, temp_globo, temp_aire, temp_bulbo, iclo, altura, peso
                        )  
                        # ---------------------------
                        # 1) DETERMINAR NIVEL Y COLOR ACTUAL
                        # ---------------------------
                        # Determinar nivel y color actual
                        if isc <= 10:
                            nivel_actual = "Confort"
                            color_actual = "green"
                        elif isc <= 30:
                            nivel_actual = "Suave"
                            color_actual = "yellow"
                        elif isc <= 40:
                            nivel_actual = "Alarma" 
                            color_actual = "orange"
                        elif isc <= 79:
                            nivel_actual = "Severa"
                            color_actual = "orange"
                        elif isc <= 100:
                            nivel_actual = "Muy Severa"
                            color_actual = "red"
                        else:
                            nivel_actual = "Crítica"
                            color_actual = "red"

                        # ---------------------------
                        # VERSIÓN CORREGIDA
                        # ---------------------------

                        st.title("🔥 Índice de Sobrecarga Calórica (ISC)")

                        # Tarjeta principal con el valor del ISC - SIN DELTA
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            # Mostrar el valor sin delta (para eliminar la flecha verde)
                            st.metric(
                                label="**ISC ACTUAL**",
                                value=f"{isc:.1f}%"
                            )
                            
                            # Mostrar el nivel con color personalizado
                            st.markdown(f"**Nivel:** <span style='color:{color_actual}; font-weight:bold;'>{nivel_actual}</span>", 
                                        unsafe_allow_html=True)

                        with col2:
                            # Indicador visual mejorado - SIN BARRA DE PROGRESO AZUL
                            st.write(f"**Progreso hacia el límite crítico (100%):**")
                            
                            if isc <= 100:
                                # Para valores normales, usar un texto simple
                                st.info(f"🟢 **{isc:.1f}% / 100%** - Dentro del límite seguro")
                            else:
                                # Para valores críticos, mostrar claramente el exceso
                                st.error(f"🔴 **100% + {isc-100:.1f}% EXCEDIDO** - CONDICIÓN CRÍTICA")
                                

                        # Línea separadora
                        st.markdown("---")

                        # CLASIFICACIÓN Y ALERTA PRINCIPAL
                        st.subheader("📊 Clasificación y Estado")

                        if nivel_actual == "Confort":
                            st.success(f"## ✅ {clasificacion_isc}")
                            st.info("**Estado:** Confort térmico - Condiciones normales de trabajo")
                            
                        elif nivel_actual == "Suave":
                            st.info(f"## ℹ️ {clasificacion_isc}")
                            st.info("**Recomendación:** Monitoreo preventivo recomendado")
                            
                        elif nivel_actual == "Alarma":
                            st.warning(f"## ⚠️ {clasificacion_isc}")
                            st.warning("**Alerta:** Inicio de zona de alarma - Implementar controles básicos")
                            
                        elif nivel_actual == "Severa":
                            st.warning(f"## 🚨 {clasificacion_isc}")
                            st.warning("**Alerta:** Controles activos requeridos - Monitoreo continuo")
                            
                        elif nivel_actual == "Muy Severa":
                            st.error(f"## 🔴 {clasificacion_isc}")
                            st.error("**Alerta:** Límite máximo permisible - Precaución extrema")
                            
                        else:  # Crítica
                            st.error(f"## 🚨 {clasificacion_isc}")
                            st.error("**ALERTA CRÍTICA:** Condiciones peligrosas - Intervención inmediata")

                        # INFORMACIÓN DE TIEMPO DE EXPOSICIÓN
                        st.markdown("---")
                        st.subheader("⏱️ Tiempo de Exposición")

                        if isc <= 100:
                            st.success("""
                            ### ✅ No se requiere limitar el tiempo de exposición
                            
                            **Explicación:** El cuerpo puede disipar el calor acumulado manteniéndose 
                            dentro de los límites fisiológicos seguros (ISC ≤ 100%).
                            """)
                        else:
                            if tiempo_exp_per != float('inf') and tiempo_exp_per > 0:
                                horas = int(tiempo_exp_per // 60)
                                minutos = int(tiempo_exp_per % 60)
                                
                                if horas > 0:
                                    tiempo_formateado = f"{horas}h {minutos}min"
                                else:
                                    tiempo_formateado = f"{minutos} min"
                                
                                st.error(f"""
                                ### 🚨 TIEMPO LÍMITE DE EXPOSICIÓN: {tiempo_formateado}
                                
                                **Advertencia Crítica:** ISC del {isc:.1f}% supera el límite seguro del 100%.
                                El cuerpo está acumulando calor activamente.
                                
                                **Acciones inmediatas requeridas:**
                                - Limitar exposición continua a **{tiempo_formateado}**
                                - Programar pausas de recuperación obligatorias
                                - Monitorear signos de estrés térmico continuamente
                                - Considerar rotación de personal
                                """)
                                
                                # Métricas rápidas
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Índice de Sobrecarga", f"{isc:.1f}%")
                                with col2:
                                    st.metric("Tiempo Límite", tiempo_formateado)
                                    
                            else:
                                st.error("""
                                ### ⚠️ CONDICIÓN EXTREMADAMENTE PELIGROSA
                                
                                **Advertencia:** El cálculo indica condiciones críticas donde no se puede 
                                determinar un tiempo seguro de exposición.
                                
                                **Acción inmediata:** Suspender actividades y evacuar el área.
                                """)

                        # LEYENDA DE NIVELES (opcional)
                        with st.expander("📋 Ver escala de niveles ISC"):
                            st.write("""
                            **Escala del Índice de Sobrecarga Calórica:**
                            
                            - 🟢 **Confort (0-10%):** Condiciones normales
                            - 🔵 **Suave (10-30%):** Monitoreo preventivo  
                            - 🟠 **Alarma (30-40%):** Inicio de controles
                            - 🟠 **Severa (40-79%):** Controles activos
                            - 🔴 **Muy Severa (80-100%):** Límite máximo
                            - 💀 **Crítica (>100%):** Intervención inmediata
                            """)
                
            if estado == "Discomfort":
                if radiacion_solar == "No":
                    st.write("### Método de evaluación: Fanger")
                    st.write("Ya que el trabajador no se encuentra en estrés térmico, se recomienda utilizar el método de evaluación Fanger.")
                    st.write("Para el método Fanger es necesario indicar el trabajo externo, la temperatura radiante media y el factor clo de la ropa.")
                    trabajo = st.number_input("Ingrese el trabajo externo (W/m²)", min_value=0, max_value=600, value=0, step=10)
                    temp_radiante_media = st.number_input("Ingrese la temperatura radiante media (°C)",min_value=10,max_value=40,value=18,step=1)
                    conjuntos_clofanger = lista_clofanger.iloc[:, 0].tolist()
                    seleccion_clofanger = st.selectbox("Seleccione el conjunto que utilizan los trabajadores:",conjuntos_clofanger
                    )
                    iclofanger = lista_clofanger[lista_clofanger["Ropa diaria"] == seleccion_clofanger]["clo"].iloc[0]
                    mostrar_fanger = st.button("Calcular Fanger")
                    # -------------------------
                    # CÁLCULO FANGER
                    # -------------------------
                    if mostrar_fanger:
                        resultado_pmv, resultado_ppd = fanger(iclofanger,carga_metabolica,trabajo,temp_aire,temp_radiante_media,velocidad_aire,humedad_relativa,None
                        )
                        st.success("✅ Cálculo del Método Fanger completado exitosamente.")

                        # -------------------------
                        # CLASIFICACIÓN PMV
                        # -------------------------
                        if resultado_pmv <= -3:
                            nivel_actualf = "Frío"
                            color_actual = "blue"
                        elif resultado_pmv <= -2:
                            nivel_actualf = "Fresco"
                            color_actual = "deepskyblue"
                        elif resultado_pmv <= -1:
                            nivel_actualf = "Ligeramente fresco"
                            color_actual = "orange"
                        elif resultado_pmv == 0:
                            nivel_actualf = "Neutro"
                            color_actual = "green"
                        elif resultado_pmv <= 1:
                            nivel_actualf = "Ligeramente caluroso"
                            color_actual = "yellow"
                        elif resultado_pmv <= 2:
                            nivel_actualf = "Caluroso"
                            color_actual = "orange"
                        elif resultado_pmv <= 3:
                            nivel_actualf = "Muy caluroso"
                            color_actual = "red"
                        else:
                            nivel_actualf = "Fuera de escala"
                            color_actual = "black"


                        # BARRA VISUAL PMV
                
                        posicion = max(0, min(100, ((resultado_pmv + 3) / 6) * 100))
                        st.markdown("### Voto Medio Estimado (PMV)")
                        st.write(f"**Nivel térmico:** {nivel_actualf}")
                        
                        progreso = max(0, min(100, ((resultado_pmv + 3) / 6) * 100))
                        if resultado_pmv <= -1:
                            color = "#3498db"  # azul
                        elif -1 < resultado_pmv < 1:
                            color = "#2ecc71"  # verde
                        else:
                            color = "#e74c3c"  # rojo

                        st.markdown(
                            f"""
                            <div style="
                                background-color:#ddd;
                                border-radius:10px;
                                height:25px;
                                width:100%;
                            ">
                                <div style="
                                    background-color:{color};
                                    width:{progreso}%;
                                    height:100%;
                                    border-radius:10px;
                                    text-align:center;
                                    color:white;
                                    font-weight:bold;
                                ">
                                    {resultado_pmv:.2f}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )     
                        # -------------------------
                        # ADECUACIÓN AMBIENTAL
                        # -------------------------
                        if -0.5 <= resultado_pmv <= 0.5:
                            st.success("La situación es ambientalmente ADECUADA")
                        else:
                            st.error("La situación es ambientalmente INADECUADA")

                        # -------------------------
                        # # SECCIÓN PPD
                        # -------------------------
                        st.markdown("## Porcentaje de Insatisfechos (PPD)")
                        st.write("Estimación de trabajadores insatisfechos y satisfechos")
                        insatisfechos = resultado_ppd
                        satisfechos = 100 - resultado_ppd
                        # Barra Insatisfechos (roja suave)
                        st.markdown("### 😥Insatisfechos")
                        st.markdown(
                                f"""
                                <div style="
                                    background-color: #e8caca;
                                    padding: 15px;
                                    border-radius: 8px;
                                    text-align: center;
                                    font-size: 22px;
                                    font-weight: bold;
                                    color: #a94442;">
                                    {insatisfechos:.2f} %
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        #Espacio visual
                        st.write("")

                        # Barra Satisfechos (verde)
                        st.markdown("### 🙂 Satisfechos")
                        st.markdown(
                                f"""
                                <div style="
                                    background-color: #5cb85c;
                                    padding: 15px;
                                    border-radius: 8px;
                                    text-align: center;
                                    font-size: 22px;
                                    font-weight: bold;
                                    color: white;">
                                    {satisfechos:.2f} %
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

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
            df_p["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_convert('America/Costa_Rica').dt.tz_localize(None)
            st.session_state["df_p"]           = df_p
            st.session_state["datos_cargados"] = True
            st.session_state["fecha_min"]      = df_p["created_at"].min().date()
            st.session_state["fecha_max"]      = df_p["created_at"].max().date()
            st.session_state["ts_temp_aire"]        = df_p["temp_seca"].mean()
            st.session_state["ts_temp_globo"]       = df_p["temp_globo"].mean()
            st.session_state["ts_humedad_relativa"] = df_p["humedad_relativa"].mean()
            st.session_state["ts_temp_bulbo"]       = None   # No viene del sensor, mantiene default
            st.session_state["ts_velocidad_aire"]   = None   # No viene del sensor, mantiene default

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