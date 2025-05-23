import streamlit as st
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Importar la función desde el archivo funciones.py
from Funciones import indice_de_sudoracion
from Funciones import tgbh
from Funciones import indice_sobrecarga_calorica



#Importar csv con datos de metabolismo, cavs y clo
lista_cavs= pd.read_csv("CAVS.csv")
lista_metabolismo= pd.read_csv("Metabolismo.csv")
lista_clo=pd.read_csv("Aislamiento.csv")

#Importar csv
lista_cavs= pd.read_csv("CAVS.csv")
lista_metabolismo= pd.read_csv("Metabolismo.csv")
lista_clo=pd.read_csv("Aislamiento.csv")

#Inicio programa Streamlit
st.title("Sistema de Monitoreo de Estrés Térmico")

st.write("Bienvenido al sistema CALA, porfavor complete la información solicitada a continuación para comenzar la evaluación")

#Definición de variables necesarias
st.write("## Datos de entrada")

#Variables ambientales

st.write( "### Variables ambientales")
st.write("Por favor cargue en este espacio un archivo CSV con los datos de ambientales. La temperatura debe estar en °C y la velocidad en m/s.")
st.write("El archivo debe contener las siguientes columnas:")
st.write("Temperatura seca, Temperatura de bulbo humedo, Temperatura de globo, Velocidad del aire")

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

#Valida si se cargó un archivo o no. En caso de no cargar un archivo se solicitará el ingreso manual de los datos
if archivo is not None:
    datos_ambientales= pd.read_csv(archivo) #Lectura del archivo
    # Mostrar los datos
    st.subheader("Vista previa del archivo:")
    st.dataframe(datos_ambientales)
    #Es necesario estandarizar el nombre de los encabezados de columna o bien el orden en que se encuentran, de momento se trabajara con nombres especificos
    try: 
        temp_aire= datos_ambientales["Temperatura seca"].mean()
    except:
        st.warning("No se encontró la columna 'Temperatura seca' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 32 °C que podrá modificar")
        temp_aire= st.number_input("#### Temperatura seca (°C)", min_value=15.00, max_value=44.00, value=32.00) #ajustar max y default
    try:
        temp_globo= datos_ambientales["Temperatura de globo"].mean()
    except:
        st.warning("No se encontró la columna 'Temperatura de globo' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 36 °C que podrá modificar")
        temp_globo= st.number_input("#### Temperatura de globo (°C)", min_value=15.00, max_value=45.00, value=36.00) #ajustar max y default
    try:
        temp_bulbo= datos_ambientales["Temperatura de bulbo humedo"].mean()
    except:
        st.warning("No se encontró la columna 'Temperatura de bulbo humedo' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 28 °C que podrá modificar")
        temp_bulbo= st.number_input("#### Temperatura de bulbo humedo (°C)", min_value=15.00, max_value=45.00, value=28.00) #ajustar max y default
    try:
        velocidad_aire= datos_ambientales["Velocidad del aire"].mean()
    except:
        st.warning("No se encontró la columna 'Velocidad del aire' en el archivo. Asegúrate de que el archivo contenga esta columna. De lo contrario, se asignará un valor por default de 0.016 m/s que podrá modificar")
        velocidad_aire= st.number_input("#### Velocidad del aire (m/s)", min_value=0.000, max_value=3.00, value=0.016) #ajustar max y default
    st.write("Los datos ambientales del aire han sido cargados correctamente, porfavor verifique que los datos sean correctos")
    
else:
    st.write("Si no cuenta con un archivo CSV, porfavor ingrese los datos manualmente en el siguiente espacio")
    col1,col2=st.columns(2)
    with col1:
        temp_aire = st.number_input("#### Temperatura seca (°C)", min_value=15.00, max_value=44.00,value=32.00)
        temp_globo = st.number_input("#### Temperatura de globo (°C)", min_value=15.00, max_value=45.00,value=36.00 )
        
    with col2:
        temp_bulbo = st.number_input("#### Temperatura de bulbo humedo (°C)", min_value=15.00, max_value=45.00, value=28.00)
        velocidad_aire = st.number_input("#### Velocidad del aire (m/s)", min_value=0.000, max_value=3.00, value=0.016)
        
#Caracteristicas de la tarea
st.write("### Caracteristicas de la tarea")
col3,col4=st.columns(2)
with col3:
    postura = st.selectbox("Selecciona una postura de trabajo", ["De pie", "Sentado", "Agachado"])
    aclimatacion = st.selectbox("¿Los trabajadores están aclimatados?", ["Si", "No"])
with col4:
    radiacion_solar = st.selectbox("¿Estan expuestos al sol?", ["Si", "No"])
    capucha = st.selectbox("¿Los trabajadores usan capucha?", ["No", "Si"])
    
    
st.write("### Aislamiento térmico de la ropa")

#Determinación de Cavs
st.write("Acontinuación se le presentarán una serie de conjuntos para determinar el valor de CAVS, esto es necesario para calcular el TGBH")
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
carga_metabolica=st.selectbox("Seleccione la tasa metabolica:",tasas)



# Calcular e imprimir los resultados
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
fig, ax = plt.subplots(figsize=(8, 6))
# Graficar las curvas
ax.plot(x_values, y_aclimatada, label="Personas Aclimatadas", color="blue", linewidth=2)
ax.plot(x_values, y_no_aclimatada, label="Personas No Aclimatadas", color="red", linestyle='--', linewidth=2)
# Graficar el punto
ax.scatter(carga_metabolica, tgbh_efectivo, color="green", zorder=5, label=f'Punto ({carga_metabolica},{round(tgbh_efectivo),2})')
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

#Compuerta lógica para mostrar métodos de evaluación
#Si se encuentra en estrés térmico, mostrará el método de evaluación SWreq e ISC, de lo contrario, mostrará Fanger. Fanger aun no se ha agregado.

if estado == "Estrés Térmico":
    st.write("### Método de evaluación: SWreq e ISC")
    st.write("Ya que el trabajador se encuentra en estrés térmico, se recomienda utilizar el método de evaluación SWreq e ISC")
    #Selección de la vestimenta para el factor clo
    st.write("A continuación se le presentarán una serie de conjuntos de ropa para determinar el valor de clo, esto es necesario para calcular el ISC y SWreq")
    conjuntos_clo= lista_clo.iloc[:,0].tolist()
    seleccion_clo= st.selectbox("Seleccione el conjunto que utilizan los trabajadores:",conjuntos_clo)
    iclo=lista_clo[lista_clo["Ropa de trabajo"]==seleccion_clo]["m²·K/W"].iloc[0]
    #SWreq
    # Crear un botón para calcular y mostrar los resultados 
    mostrar_swreq=st.button("Calcular Índice de sudoración requerida")
    if mostrar_swreq:
    
        # Llamar a la función indice de suodración
        dle_alarma_q, dle_peligro_q, dle_alarma_d, dle_peligro_d = indice_de_sudoracion(temp_aire, temp_globo, temp_bulbo, iclo, carga_metabolica, velocidad_aire, postura, aclimatacion)
       #Pasar DLE a horas y min
       
        #DLE Alarma Q
        horas_dle_alarma_q=int(dle_alarma_q//60)
        minutos_dle_alarma_q=int(dle_alarma_q%60)
        #DLE Peligro Q
        horas_dle_peligro_q=int(dle_peligro_q//60)
        minutos_dle_peligro_q=int(dle_peligro_q%60)
        
        #DLE Alarma D
        horas_dle_alarma_d=int(dle_alarma_d//60)
        minutos_dle_alarma_d=int(dle_alarma_d%60)
        #DLE Peligro D
        horas_dle_peligro_d=int(dle_peligro_d//60)
        minutos_dle_peligro_d=int(dle_peligro_d%60)
        
         #Mostrar los resultados
        st.write("### Resultados SWreq")
        st.write(f"⏱️ DLE Alarma Q: {horas_dle_alarma_q}h {minutos_dle_alarma_q}min")
        st.write(f"⏱️ DLE Peligro Q: {horas_dle_peligro_q}h {minutos_dle_peligro_q}min")
        st.write(f"⏱️ DLE Alarma D: {horas_dle_alarma_d}h {minutos_dle_alarma_d}min")
        st.write(f"⏱️ DLE Peligro D: {horas_dle_peligro_d}h {minutos_dle_peligro_d}min")
        
        
    #ISC
    mostrar_isc=st.button("Calcular Índice de Sobrecarga de Calor")
    if mostrar_isc:
        st.write("### Resultados ISC")
        #Llamar a la función indice de sudoracion
        isc,clasificacion_isc, tiempo_exp_per=indice_sobrecarga_calorica(carga_metabolica,velocidad_aire,temp_globo,temp_aire, temp_bulbo,iclo)  
        st.write(f"El indice de sobrecarga calórica es: {round(isc,2)} %")
        st.write(f"Clasificación de la sobrecarga calórica:  {clasificacion_isc}")
        horas_exp_isc=int(tiempo_exp_per//60)
        minutos_exp_isc=int(tiempo_exp_per%60)
        st.write(f"⏱️ Tiempo de exposición permitido: {horas_exp_isc}h {minutos_exp_isc}min")
        
if estado== "Discomfort":
    st.write("### Método de evaluación: Fanger")
    st.write("Ya que el trabajador no se encuentra en estrés térmico, se recomienda utilizar el método de evaluación Fanger")
    #Llamar a la función indice de sudoracion
    st.write("Aun no se ha implementado el método de evaluación Fanger, porfavor vuelva más tarde para poder utilizarlo")        
