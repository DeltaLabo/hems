import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import altair as alt
import math 

# Importar la función desde el archivo funciones.py
from Funciones import indice_de_sudoracion
from Funciones import tgbh
from Funciones import indice_sobrecarga_calorica
from Funciones import format_time
from Funciones import indice_de_calor

#Importar csv con datos de metabolismo, cavs y clo
lista_cavs= pd.read_csv("CAVS.csv")
lista_metabolismo= pd.read_csv("Metabolismo.csv")
lista_clo=pd.read_csv("Aislamiento.csv")


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
st.header("Bienvenido al Sistema HEMS")
st.write("""
Complete la información solicitada a continuación para comenzar la evaluación de estrés térmico 
en el ambiente laboral. Este sistema le permitirá analizar las condiciones térmicas y obtener 
recomendaciones para proteger la salud de los trabajadores.
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
st.write("## Datos de entrada")

#Variables ambientales

st.write( "### Variables ambientales")
st.write("Por favor cargue en este espacio un archivo CSV con los datos de ambientales. La temperatura debe estar en °C y la velocidad en m/s.")
st.write("Los archivos CSV (Comma Separated Value) pueden obtenerse al indicarle a excel que guarde un archivo en este formato, asegurandose de que contenga una sola hoja, con los nombres de columna apropiados y numeros con decimales con punto")
st.write("El archivo debe contener las siguientes columnas nombradas tal y como se indica a continuación:")
st.write("Temperatura seca, Temperatura de bulbo humedo, Temperatura de globo, Velocidad del aire, Presión atmosférica, Humedad relativa")

#Datos default
temp_aire=  32.00 #ajustar default
temp_globo= 36.00 #ajustar default
temp_bulbo= 28.00   #ajustar default
velocidad_aire= 0.016 #ajustar default
presion_aire= 101.3 #ajustar default
humedad_relativa= 50.00 #ajustar default

#Carga del csv
try:
    archivo = st.file_uploader("Sube tu archivo CSV", type=["csv"])
except: 
    st.warning("No se pudo cargar el archivo. Asegúrate de que el archivo sea un CSV y contenga las columnas requeridas.")
    archivo = None




    # Mostrar los datos
    st.subheader("Vista previa del archivo:")
    st.dataframe(archivo)
    #Es necesario estandarizar el nombre de los encabezados de columna o bien el orden en que se encuentran, de momento se trabajara con nombres especificos
    #Validar si falta alguna columna
    try: 
        temp_aire= archivo["Temperatura seca"].mean()
    except:
        st.warning("No se encontró la columna 'Temperatura seca' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 32 °C que podrá modificar")
        temp_aire= st.number_input("#### Temperatura seca (°C)", min_value=15.00, max_value=44.00, value=32.00) #ajustar max y default
    try:
        temp_globo= archivo["Temperatura de globo"].mean()
    except:
        st.warning("No se encontró la columna 'Temperatura de globo' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 36 °C que podrá modificar")
        temp_globo= st.number_input("#### Temperatura de globo (°C)", min_value=15.00, max_value=45.00, value=36.00) #ajustar max y default
    try:
        temp_bulbo= archivo["Temperatura de bulbo humedo"].mean()
    except:
        st.warning("No se encontró la columna 'Temperatura de bulbo humedo' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 28 °C que podrá modificar")
        temp_bulbo= st.number_input("#### Temperatura de bulbo humedo (°C)", min_value=15.00, max_value=45.00, value=28.00) #ajustar max y default
    try:
        velocidad_aire= archivo["Velocidad del aire"].mean()
    except:
        st.warning("No se encontró la columna 'Velocidad del aire' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 0.016 m/s que podrá modificar")
        velocidad_aire= st.number_input("#### Velocidad del aire (m/s)", min_value=0.000, max_value=3.00, value=0.016) #ajustar max y default
    try:
        presion_aire= archivo["Presión atmosférica"].mean()
    except: 
        st.warning("No se encontró la columna 'Presión atmosférica' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 101.3 kPa que podrá modificar")
        presion_aire= st.number_input("#### Presión atmosférica (kPa)", min_value=80.00, max_value=120.00, value=101.3) #ajustar max y default
    try:
        humedad_relativa= archivo["Humedad relativa"].mean()    
    except:
        st.warning("No se encontró la columna 'Humedad relativa' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 50 % que podrá modificar")
        humedad_relativa= st.number_input("#### Humedad relativa (%)", min_value=10.00, max_value=100.00, value=50.00) #ajustar max y default
    st.write("Los datos ambientales del aire han sido cargados correctamente, porfavor verifique que los datos sean correctos")
    
else:
    st.write("Si no cuenta con un archivo CSV, porfavor ingrese los datos manualmente en el siguiente espacio")
    col1,col2=st.columns(2)
    with col1:
        temp_aire = st.number_input("#### Temperatura seca (°C)", min_value=15.00, max_value=44.00,value=32.00)
        temp_globo = st.number_input("#### Temperatura de globo (°C)", min_value=15.00, max_value=45.00,value=36.00 )
        humedad_relativa = st.number_input("#### Humedad relativa (%)", min_value=10.00, max_value=100.00, value=50.00)
        
    with col2:
        temp_bulbo = st.number_input("#### Temperatura de bulbo humedo (°C)", min_value=15.00, max_value=45.00, value=28.00)
        velocidad_aire = st.number_input("#### Velocidad del aire (m/s)", min_value=0.000, max_value=3.00, value=0.016)
        presion_aire = st.number_input("#### Presión atmosférica (kPa)", min_value=80.00, max_value=120.00, value=101.3)
        
        
#Caracteristicas de la tarea
st.write("### Caracteristicas de la tarea")
st.write("Indique los siguientes aspectos relacionados a las caracteristicas de la tarea")
col3,col4=st.columns(2)
with col3:
    postura = st.selectbox("Selecciona una postura de trabajo", ["De pie", "Sentado", "Agachado"])
    aclimatacion = st.selectbox("¿Los trabajadores están aclimatados?", ["Si", "No"])
    conveccion = st.selectbox("¿Que tipo de ventilación tiene el área de trabajo?", ["Natural", "Forzada"])
with col4:
    radiacion_solar = st.selectbox("¿Estan expuestos al sol?", ["Si", "No"])
    capucha = st.selectbox("¿Los trabajadores usan capucha?", ["No", "Si"])
    
    
st.write("### Aislamiento térmico de la ropa")

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
st.write("### Tasa metabólica")

st.write("Ahora es necesario indicar el metabolismo. Seleccione una tasa metábolica que se ajuste a la labor.")

st.dataframe(lista_metabolismo)
tasas=lista_metabolismo.iloc[:,1].tolist()
carga_metabolica=st.number_input("Ingrese la tasa metabólica (W/m²)", min_value=100, max_value=600, value=160, step=10)



# Calcular e imprimir los resultados

#Indice de Calor
#Llamar a la función indice de calor
st.write("### Resultados Índice de Calor")
heat_index,nivel,efecto,medidas_de_salud=indice_de_calor(temp_aire,humedad_relativa)

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
with st.expander(f"📋 Ver medidas de prevención para {nivel}", expanded=False):
    st.write(f"**Medidas específicas para {nivel}:**")
    
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
wbgt,tgbh_efectivo,tgbh_ref,estado=tgbh(radiacion_solar,temp_aire,temp_globo,temp_bulbo,cavs,carga_metabolica,aclimatacion)
# Mostrar los valores asignados después de que el usuario presione el botón
st.write("### Resultados TGBH")
st.write(f"TGBH: {round(wbgt,2)}")
st.write(f"TGBHm efectivo: {round(tgbh_efectivo,2)}")
st.write(f"TGBHm referencia: {round(tgbh_ref,2)}")
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
    mostrar_swreq = st.button("Calcular Índice de sudoración requerida")
    if mostrar_swreq:
        
        # Llamar a la función indice de sudoración
        dle_alarma_q, dle_peligro_q, dle_alarma_d, dle_peligro_d = indice_de_sudoracion(temp_aire, temp_globo, temp_bulbo, iclo, carga_metabolica, velocidad_aire, postura, aclimatacion, conveccion)
        
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
        
