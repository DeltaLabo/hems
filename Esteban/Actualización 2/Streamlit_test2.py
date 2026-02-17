import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
import math 

# Importar la función desde el archivo funciones.py
from funciones import indice_de_sudoracion, tgbh, indice_sobrecarga_calorica, format_time, indice_de_calor

#Importar csv con datos de metabolismo, cavs y clo
lista_cavs = pd.read_csv("data/CAVS.csv")
lista_metabolismo = pd.read_csv("data/Metabolismo.csv")
lista_clo = pd.read_csv("data/Aislamiento.csv")

# Configuración inicial de la página
st.set_page_config(
    page_title="Sistema HEMS - Evaluación de Estrés Térmico",
    page_icon="🔥",
    layout="centered"
)

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
    
    **Métodos de Evaluación Implementados:**
    - **Índice de Calor (Heat Index):** Evalúa la percepción del calor considerando temperatura y humedad
    - **TGBH (Temperatura de Globo y Bulbo Húmedo):** Temperatura de globo y bulbo húmedo para estrés térmico
    - **SWreq (Índice de Sudoración Requerida):** Calcula la sudoración necesaria para el equilibrio térmico y tiempos límite de exposición
    - **ISC (Índice de Sobrecarga Calórica):** Evalúa la carga calórica acumulada en el cuerpo
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

#Variables ambientales

st.write("### 🌍 Variables ambientales")
st.write("Puede cargar un archivo CSV o ingresar los datos manualmente:")
st.write("**📁 Columnas requeridas en el CSV:**")
st.write("""
**Para mayor facilidad, puede COPIAR Y PEGAR estos nombres exactos en su archivo CSV:**

Temperatura seca (°C), Temperatura de bulbo humedo (°C) ,Temperatura de globo (°C), Velocidad del aire (m/s), Humedad relativa (%)
"""
)
# 1. File uploader simple
archivo = st.file_uploader("Sube tu archivo CSV con datos ambientales", type=["csv"], 
                          help="El archivo debe contener columnas: 'Temperatura seca', 'Temperatura de globo', 'etc' ")

# Valores por defecto
temp_aire, temp_globo, temp_bulbo = 32.00, 36.00, 28.00
velocidad_aire, humedad_relativa = 0.016, 50.00

# 2. Procesar archivo si existe
# REEMPLAZAR todo el bloque de procesamiento de archivos con esto:

# Procesar archivo si existe
if archivo is not None:
    try:
        df = pd.read_csv(archivo)
        st.success("✅ Archivo cargado correctamente")
        
        # Vista previa
        st.write("**Vista previa (primeras 5 filas):**")
        st.dataframe(df.head())
        
        # Diccionario para mapear columnas con valores por defecto
        columnas_map = {
            "Temperatura seca (°C)": ("temp_aire", 32.00),
            "Temperatura de globo (°C)": ("temp_globo", 36.00), 
            "Temperatura de bulbo humedo (°C)": ("temp_bulbo", 28.00),
            "Velocidad del aire (m/s)": ("velocidad_aire", 0.016),
            "Humedad relativa (%)": ("humedad_relativa", 50.00)
        }
        
        # Procesar cada columna de forma SEGURA
        columnas_encontradas = []
        columnas_faltantes = []
        columnas_vacias = []
        
        for columna_df, (variable, valor_default) in columnas_map.items():
            if columna_df in df.columns:
                # Verificar si la columna tiene datos NO vacíos
                if not df[columna_df].isna().all() and len(df[columna_df].dropna()) > 0:
                    # Calcular promedio excluyendo NaN
                    valor_promedio = df[columna_df].mean()
                    
                    # Verificar si el resultado es NaN (por si acaso)
                    if pd.isna(valor_promedio):
                        globals()[variable] = valor_default
                        columnas_vacias.append(columna_df)
                    else:
                        globals()[variable] = valor_promedio
                        columnas_encontradas.append(columna_df)
                else:
                    # Columna existe pero está vacía
                    globals()[variable] = valor_default
                    columnas_vacias.append(columna_df)
            else:
                # Columna no existe en el CSV
                globals()[variable] = valor_default
                columnas_faltantes.append(columna_df)
        
        # MOSTRAR RESUMEN DETALLADO
        st.write("### 📋 Resumen de Datos Cargados")
        
        if columnas_encontradas:
            st.write("**✅ Datos obtenidos del archivo:**")
            for columna in columnas_encontradas:
                variable = columnas_map[columna][0]
                valor = globals()[variable]
                st.write(f"• {columna}: **{valor:.2f}**")
        
        if columnas_vacias:
            st.warning("**⚠️ Columnas vacías (usando valores por defecto):**")
            for columna in columnas_vacias:
                st.write(f"• {columna}")
        
        if columnas_faltantes:
            st.error("**❌ Columnas faltantes (usando valores por defecto):**")
            for columna in columnas_faltantes:
                st.write(f"• {columna}")
        
        # Información importante para el usuario
        if columnas_vacias or columnas_faltantes:
            st.info("""
            **💡 Información importante:**
            - Las columnas **vacías o faltantes** usan valores por defecto
            - Puede **corregir manualmente** cualquier valor en la siguiente sección
            """)
        
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.info("📝 Por favor, ingrese los datos manualmente")
else:
    st.info("📝 Modo de entrada manual - ingrese los datos a continuación")

# 3. Inputs manuales (siempre visibles)
# INPUTS MANUALES (siempre visibles y pre-llenados)
st.write("### ✏️ Ingreso manual de Datos Ambientales")
st.write("Verifique o modifique los valores a continuación:")

col1, col2 = st.columns(2)
with col1:
    temp_aire = st.number_input("Temperatura seca (°C)", min_value=15.00, max_value=60.00, value=float(temp_aire))
    temp_globo = st.number_input("Temperatura de globo (°C)", min_value=15.00, max_value=80.00, value=float(temp_globo))
    humedad_relativa = st.number_input("Humedad relativa (%)", min_value=10.00, max_value=100.00, value=float(humedad_relativa))
    
with col2:
    temp_bulbo = st.number_input("Temperatura de bulbo húmedo (°C)", min_value=15.00, max_value=60.00, value=float(temp_bulbo))
    velocidad_aire = st.number_input("Velocidad del aire (m/s)", min_value=0.000, max_value=10.00, value=float(velocidad_aire))
    
        
        
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
if radiación_solar == "Si":
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
         altura=st.number_input("Altura promedio de los trabajadores (cm)", min_value=0.00, max_value=300.00, value=170.00)
    with col6:
        peso=st.number_input("Peso promedio de los trabajadores (kg)", min_value=50.00, max_value=150.00, value=70.00)
    
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
    
if estado== "Discomfort":
    if radiacion_solar== "No":
        st.write("### Método de evaluación: Fanger")
        st.write("Ya que el trabajador no se encuentra en estrés térmico, se recomienda utilizar el método de evaluación Fanger")
        #Llamar a la función Fanger
        st.write("Aun no se ha implementado el método de evaluación Fanger, porfavor vuelva más tarde para poder utilizarlo")    
    else: 
        st.write("No se cuenta con una metodologia para evaluar discomfort en exteriores")
