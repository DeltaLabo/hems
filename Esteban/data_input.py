import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

#Importar csv con datos de metabolismo, cavs y clo
lista_cavs= pd.read_csv("CAVS.csv")
lista_metabolismo= pd.read_csv("Metabolismo.csv")
lista_clo=pd.read_csv("Aislamiento.csv")

#Inicio programa Streamlit
st.title("Sistema de Monitoreo de Estrés Térmico")

st.write("Bienvenido al sistema CALA, porfavor complete la información solicitada a continuación para comenzar la evaluación")

#Definición del identificador de la tarea para el dashboard
st.write("## Identificador de la tarea")
st.write("Por favor ingrese un identificador único para la tarea que se está evaluando, esto es necesario para el correcto funcionamiento del dashboard")
st.write("Coloque el nombre de su empresa seguido de un guión y una breve descripción de la tarea, por ejemplo: EmpresaX-TareaY")
identificador= st.text_input("Identificador de la tarea")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

#Definición de variables necesarias
st.write("## Datos de entrada")

#Caracteristicas de la tarea
st.write("### Caracteristicas de la tarea")
col3,col4=st.columns(2)
with col3:
    postura = st.selectbox("Selecciona una postura de trabajo", ["De pie", "Sentado", "Agachado"])
    aclimatacion = st.selectbox("¿Los trabajadores están aclimatados?", ["Si", "No"])
    conveccion = st.selectbox("¿Que tipo de ventilación tiene el área de trabajo?", ["Natural", "Forzada"])
with col4:
    radiacion_solar = st.selectbox("¿Estan expuestos al sol?", ["Si", "No"])
    capucha = st.selectbox("¿Los trabajadores usan capucha?", ["No", "Si"])
    
st.write("### Aislamiento térmico de la ropa")

st.write("En esta sección se solicitará que ingrese información sobre la vestimenta de los trabajadores, se solicita dos veces para determinar el valor de CAVS y el factor clo")
#Determinación de Cavs
st.write("Acontinuación se le presentarán una serie de conjuntos para determinar el valor de CAVS, esto es necesario para calcular el TGBH")
conjuntos_cavs= lista_cavs.iloc[:,0].tolist()
seleccion_cavs= st.selectbox("Seleccione el conjunto que utilizan los trabajadores:",conjuntos_cavs)
cavs=lista_cavs[lista_cavs["Conjunto"]==seleccion_cavs]["CAV"].iloc[0]
if capucha == "Si": 
    cavs +=1
st.write ("El valor de Cavs corresponde a:", cavs)

#Selección de la vestimenta para el factor clo
st.write("A continuación se le presentarán una serie de conjuntos de ropa para determinar el valor de clo, esto es necesario para calcular el ISC y SWreq")
conjuntos_clo= lista_clo.iloc[:,0].tolist()
seleccion_clo= st.selectbox("Seleccione el conjunto que utilizan los trabajadores:",conjuntos_clo)
iclo=lista_clo[lista_clo["Ropa de trabajo"]==seleccion_clo]["m²·K/W"].iloc[0]
    
#Determinación de la tasa metábolica
st.write("### Tasa metabólica")

st.write("Ahora es necesario indicar el metabolismo. Seleccione una tasa metábolica que se ajuste a la labor.")

st.dataframe(lista_metabolismo)
tasas=lista_metabolismo.iloc[:,1].tolist()
carga_metabolica=st.selectbox("Seleccione la tasa metabolica:",tasas)

#Caracteristicas de los trabajadores
st.write("### Caracteristicas de los trabajadores")
st.write("A continuación, es necesario ingresar las características de los trabajadores que realizarán la tarea.")
col1, col2 = st.columns(2)
with col1:
    peso = st.number_input("Peso (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)
    

with col2:
    altura = st.number_input("Altura (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.1)

#Guardar la tarea
st.title("Guardar la tarea")

st.write("Finalmente, es necesario guardar la tarea para que pueda ser utilizada en el dashboard, porfavor oprima el botón guardar tarea")
payload = {
    "postura": postura,
    "aclimatación": aclimatacion,
    "convección": conveccion,
    "radiación": radiacion_solar,
    "cavs": int(cavs),
    "carga_metabolica": float(carga_metabolica),
    "peso": float(peso),
    "altura": float(altura),
    "iclo": float(iclo),
    "Fecha": timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
}
#Declarar la ruta para guardar los archivos, reemplazar una vez se establezca el servidor
ruta_base = Path("C:/Repositorios/hems/Esteban/profiles")

#Nombre del archivo
nombre_archivo = f"{identificador}.json"


if st.button("💾 Guardar JSON"):
    try:
        destino = Path(ruta_base) / identificador
        destino.parent.mkdir(parents=True, exist_ok=True)  # crea la carpeta si no existe
        with destino.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        st.success(f"Archivo guardado en: {destino}")
        st.code(str(destino))
    except Exception as e:
        st.error(f"No se pudo guardar el archivo: {e}")