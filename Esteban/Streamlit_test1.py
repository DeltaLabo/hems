import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Importar la función desde el archivo funciones.py
from Funciones import indice_de_sudoracion
from Funciones import tgbh

#Importar csv
lista_cavs= pd.read_csv("CAVS.csv")
lista_metabolismo= pd.read_csv("Metabolismo.csv")
lista_clo=pd.read_csv("Aislamiento.csv")

#Inicio programa Streamlit
st.title("Sistema de Monitoreo de Estrés Térmico")

st.write("Bienvenido al sistema CALA, porfavor complete la información solicitada a continuación para comenzar la evaluación")

#Definición de variables necesarias
st.write("## Datos de entrada")

st.write( "### Variables ambientales")
col1,col2=st.columns(2)
with col1:
    temp_aire = st.number_input("#### Temperatura seca (°C)", min_value=15.00, max_value=44.00,value=32.00)
    temp_globo = st.number_input("#### Temperatura de globo (°C)", min_value=15.00, max_value=45.00,value=36.00 )
    presion_aire= st.number_input("#### Presión del aire (kPa)", min_value=0.00, max_value=100.00, value=101.3) #ajustar max y default
    
with col2:
    temp_bulbo = st.number_input("#### Temperatura de bulbo humedo (°C)", min_value=15.00, max_value=45.00, value=28.00)
    velocidad_aire = st.number_input("#### Velocidad del aire (m/s)", min_value=0.000, max_value=3.00, value=0.016)
    humedad_relativa= st.number_input("#### Humedad relativa (%)", min_value=0.00, max_value=100.00, value=50.00)#ajustar max y default

st.write("### Caracteristicas de la tarea")
col3,col4=st.columns(2)
with col3:
    postura = st.selectbox("Selecciona una postura de trabajo", ["De pie", "Sentado", "Agachado"])
    aclimatacion = st.selectbox("¿Los trabajadores están aclimatados?", ["Si", "No"])
with col4:
    radiacion_solar = st.selectbox("¿Estan expuestos al sol?", ["Si", "No"])
    capucha = st.selectbox("¿Los trabajadores usan capucha?", ["Si", "No"])

st.write("### Aislamiento térmico de la ropa")
#Determinación de iclo
st.write("A continuación se le presentarán una serie de conjuntos de ropa para determinar el valor de clo, esto es necesario para calcular el ISC y SWreq")
conjuntos_clo= lista_clo.iloc[:,0].tolist()
seleccion_clo= st.selectbox("Seleccione el conjunto que utilizan los trabajadores:",conjuntos_clo)
iclo=lista_clo[lista_clo["Ropa de trabajo"]==seleccion_clo]["m²·K/W"].iloc[0]
#Determinación de Cavs
st.write("A continuación se le presentarán una serie de conjuntos para determinar el valor de CAVS, esto es necesario para calcular el TGBH")
conjuntos_cavs= lista_cavs.iloc[:,0].tolist()
seleccion_cavs= st.selectbox("Seleccione el conjunto que utilizan los trabajadores:",conjuntos_cavs)
cavs=lista_cavs[lista_cavs["Conjunto"]==seleccion_cavs]["CAV"].iloc[0]
if capucha == "Si": 
    cavs +=1
st.write ("El valor de Cavs corresponde a:", cavs)
#Determinación de la tasa metábolica

st.write("Ahora es necesario indicar el metabolismo. Seleccione una tasa metábolica que se ajuste a la labor.")

st.dataframe(lista_metabolismo)
tasas=lista_metabolismo.iloc[:,1].tolist()
carga_metabolica=st.selectbox("Seleccione la tasa metabolica:",tasas)



# Calcular e imprimir los resultados
#TGBH
# Crear un botón para calcular y mostrar los resultados 
mostrar_tgbh=st.button("Calcular TGBH")
if mostrar_tgbh:
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
    fig, ax = plt.subplots(figsize=(8, 6))
    # Graficar las curvas
    ax.plot(x_values, y_aclimatada, label="Personas Aclimatadas", color="blue", linewidth=2)
    ax.plot(x_values, y_no_aclimatada, label="Personas No Aclimatadas", color="red", linestyle='--', linewidth=2)
    # Graficar el punto
    ax.scatter(carga_metabolica, tgbh_efectivo, color="green", zorder=5, label=f'Punto ({carga_metabolica}, {tgbh_efectivo})')
    # Etiquetas y título
    ax.set_xlabel('Carga Metabólica')
    ax.set_ylabel('WBGT Efectivo')
    ax.set_title('Curvas de Aclimatación y No Aclimatación')
    ax.legend()
    # Ajustar límites de los ejes
    ax.set_xlim(100, 600)
    ax.set_ylim(15, 45)

    # Mostrar gráfico
    st.pyplot(fig)
#SWreq
# Crear un botón para calcular y mostrar los resultados 
mostrar_swreq=st.button("Calcular Índice de sudoración requerida")
if mostrar_swreq:
    # Llamar a la función indice de suodración
    dle_alarma_q, dle_peligro_q, dle_alarma_d, dle_peligro_d = indice_de_sudoracion(temp_aire, temp_globo, temp_bulbo, iclo, carga_metabolica, velocidad_aire, postura, aclimatacion)
    #Mostrar los resultados
    st.write("### Resultados SWreq")
    st.write(f"DLE Alarma Q: {round(dle_alarma_q,2)} min")
    st.write(f"DLE Peligro Q: {round(dle_peligro_q,2)} min")
    st.write(f"DLE Alarma D: {round(dle_alarma_d,2)} min")
    st.write(f"DLE Peligro D: {round(dle_peligro_d,2)} min")
