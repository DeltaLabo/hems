import math
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

"""Función para el cálculo del índice de sobre carga calorica. (SWreq)"""

def indice_de_sudoracion(temp_aire, temp_globo, temp_bulbo, iclo, carga_metabolica, velocidad_aire, postura, aclimatacion, conveccion):
    #Definición de constantes
    BOLTZMAN = 5.67 * (10**-8)  # W/((m²)(K**4))
    EMISIVIDAD_PIEL = 0.97
     # Diccionario de posturas y sus valores correspondientes
    postura_trabajo_dict = {
        "De pie": 0.77,
        "Sentado": 0.7,
        "Agachado": 0.67
    }
    
    # Definición del Ar/Adu
    postura_trabajo = postura_trabajo_dict[postura]
    #Pasar la tasa metabolica a W/m2
    carga_metabolica=carga_metabolica/1.7
    # Cálculo de la temperatura radiante media
    if velocidad_aire > 0.15:
        temp_radiante_media = (((temp_globo + 273)**4) + (2.5 * (10**8)) * (velocidad_aire**0.6) * (temp_globo - temp_aire))**0.25 - 273
    else:
        temp_radiante_media = (((temp_globo + 273)**4) + (0.42 * (10**8)) * ((temp_globo - temp_aire)**0.25) * (temp_globo - temp_aire))**0.25 - 273
    
    presion_saturacion_bulbo = math.exp(16.653 - (4030.18 / (temp_bulbo + 235)))  # (kPa)
    presion_parcial_ambiente = presion_saturacion_bulbo - 0.0667 * (temp_aire - temp_bulbo)  # (kPa)
    temp_piel = 30 + (0.0930 * temp_aire) + (0.045 * temp_radiante_media) - (0.571 * velocidad_aire) + (0.2540 * presion_parcial_ambiente) + (0.00128 * carga_metabolica) - (3.570 * iclo)

    presion_vapor_piel = math.exp(16.653 - (4030.18 / (temp_piel + 235)))
    
    # Calcular coeficientes y factores de reducción de la vestimenta
    velocidad_aire_relativa = velocidad_aire + (0.0052 * (carga_metabolica - 58))
    if conveccion == "Natural":
        hc = 3.5 + (5.2 * velocidad_aire_relativa)
    else:
        if velocidad_aire_relativa <= 1:
            hc = 3.5 + (5.2 * velocidad_aire_relativa)
        else:
            hc = 8.7*(velocidad_aire_relativa**0.6)
    hr = (EMISIVIDAD_PIEL * BOLTZMAN * postura_trabajo * (((temp_piel + 273)**4) - ((temp_radiante_media + 273)**4))) / (temp_piel - temp_radiante_media)
    he = 16.7 * hc
    fclo = 1 + (1.970 * iclo)
    f_mayus_clo = 1 / (((hc + hr) * iclo) + (1 / fclo))
    feclo = 1 / (1 + (2.22 * hc * (iclo - ((fclo - 1) / ((hc + hr) * fclo)))))
    resistencia_total_vestido = 1 / (he * feclo)

    # Calcular Emax
    e_max = (presion_vapor_piel - presion_parcial_ambiente) / resistencia_total_vestido
    
    # Cálculos de balance térmico
    c_res = 0.0014 * carga_metabolica * (35 - temp_aire)
    e_res = 0.0173 * carga_metabolica * (5.624 - presion_parcial_ambiente)
    r = hr * f_mayus_clo * (temp_piel - temp_radiante_media)
    c = hc * f_mayus_clo * (temp_piel - temp_aire)
    e_req = carga_metabolica - c_res - e_res - c - r
    
    # Análisis del puesto
    w_p = e_req / e_max
    

    # Definir máximo de humedad y tasa de sudoración según aclimatación
    aclimatacion_dict = {
        "Si": {
            "w_max": 1.0,
            "sw_max": 500,
            "Q_max_peligro": 60,
            "Q_max_alarma": 50,
            "D_max_peligro": 2000,
            "D_max_alarma": 1500
        },
        "No": {
            "w_max": 0.85,
            "sw_max": 400,
            "Q_max_peligro": 60,
            "Q_max_alarma": 50,
            "D_max_peligro": 1250,
            "D_max_alarma": 1000
        }
    }

    w_max = aclimatacion_dict[aclimatacion]["w_max"]
    sw_max = aclimatacion_dict[aclimatacion]["sw_max"]
    q_max_peligro = aclimatacion_dict[aclimatacion]["Q_max_peligro"]
    q_max_alarma = aclimatacion_dict[aclimatacion]["Q_max_alarma"]
    d_max_peligro = aclimatacion_dict[aclimatacion]["D_max_peligro"]
    d_max_alarma = aclimatacion_dict[aclimatacion]["D_max_alarma"]
    
    if w_p > w_max:
        w_p = w_max

    e_p = w_p * e_max
    r_p = 1 - (w_p**2) / 2
    sw_p = e_p / r_p
    
    # Validar sw_p contra sw_max
    if sw_p > sw_max:
        w_p = math.sqrt((e_max / sw_max)**2 + 2) - (e_max / sw_max)
        e_p = w_p * e_max
        sw_p = sw_max
    
    # Tiempos límite de exposición
    dle_alarma_q = 60 * q_max_alarma / (e_req - e_p)
    dle_peligro_q = 60 * q_max_peligro / (e_req - e_p)
    dle_alarma_d = 60 * d_max_alarma / sw_p
    dle_peligro_d = 60 * d_max_peligro / sw_p

    return dle_alarma_q, dle_peligro_q, dle_alarma_d, dle_peligro_d

"""Función para TGBH"""
def tgbh(radiacion_solar,temp_aire,temp_globo,temp_bulbo,cavs,carga_metabolica,aclimatacion):
   
    #TGBH simple x
    if radiacion_solar == "No":
        wbgt = (0.7*temp_bulbo)+(0.3*temp_globo)
    else:
        wbgt = (0.7*temp_bulbo)+(0.2*temp_globo)+(0.1*temp_aire)
    #TGBH efectivo y
    wbgt_efectivo= wbgt + cavs
    #TGBH referencia
    if aclimatacion == "Si":
        wbgt_ref=56.7-(11.5*math.log(carga_metabolica,10))
    else: 
        wbgt_ref=59.9-(14.1*math.log(carga_metabolica,10))
    
    #determinar si estrés o discomfort
    if wbgt_efectivo>wbgt_ref:
        estado="Estrés Térmico"
    else:
        estado="Discomfort"
    return (wbgt,wbgt_efectivo,wbgt_ref,estado)

"""Función para Índice de Sobrecarga Calorica (ISC)"""

def indice_sobrecarga_calorica(carga_metabolica,velocidad_aire, temp_globo, temp_aire,temp_bulbo,iclo,altura,peso):
  
    carga_metabolica=carga_metabolica/1.7
    # Definir los valores de K según la vestimenta
    if iclo != 0:
        K_1, K_2, K_3 = 7, 4.4, 4.6
    elif iclo == 0:
        K_1, K_2, K_3 = 11.7, 7.3, 7.6
        
    
    if velocidad_aire > 0.15:
            temp_radiante_media = ((((temp_globo + 273)**4) + (2.5 * (10**8)) * (velocidad_aire**0.6) * (temp_globo - temp_aire))**0.25) - 273
    else:
            temp_radiante_media = ((((temp_globo + 273)**4) + (0.42 * (10**8))*((temp_globo - temp_aire)**0.25)*(temp_globo - temp_aire))**0.25)- 273
    # Cálculo de los términos
    presion_saturacion_bulbo = math.exp(16.653 - (4030.18 / (temp_bulbo + 235)))  # (kPa)
    presion_parcial_ambiente = (presion_saturacion_bulbo - 0.0667 * (temp_aire - temp_bulbo))  # kPa actualmente(kPa o hPa) preguntar a Adrian por esto

    calor_rad = (K_2 * (temp_radiante_media - 35))
    calor_conv = (K_3 * (velocidad_aire ** 0.6) * (temp_aire - 35))
    evaporacion_max = K_1 * (velocidad_aire** 0.6) * (56 - presion_parcial_ambiente)  
    evaporacion_req = carga_metabolica + calor_rad + calor_conv  #PREGUNTAR CUANDO SE SUMAN Y CUANDO SE RESTAN

    # Cálculo del Índice de Sobrecarga Calórica (ISC)
    indice_sobrecarga_calorica = (evaporacion_req /evaporacion_max) * 100

    # Clasificación de la sobrecarga calórica
    clasificacion_isc=0
    if 10 < indice_sobrecarga_calorica < 30:
        clasificacion_isc="Sobrecarga calórica que oscila entre suave y moderada."
    elif 40 < indice_sobrecarga_calorica < 60:
        clasificacion_isc=("Sobrecarga calórica severa")
    elif 70 < indice_sobrecarga_calorica < 90:
        clasificacion_isc=("Sobrecarga calórica muy severa")
    elif indice_sobrecarga_calorica == 100:
        clasificacion_isc=("Sobrecarga calórica máxima permisible")
    elif indice_sobrecarga_calorica > 100:
        clasificacion_isc=("Condiciones críticas por sobrecarga calórica")
        
    if evaporacion_req <= evaporacion_max:
        tiempo_exp_per = float('inf')  # Infinito si no hay sobrecarga calórica
    else:
        tiempo_exp_per=2440/(evaporacion_req-evaporacion_max)
    
    #Tiempo de recuperación
    superficie_corporal=(peso**0.425)*(altura**0.725)*0.007184
    tiempo_de_recuperacion= (58+peso*1)/((evaporacion_max-evaporacion_req)*superficie_corporal) #minutos

    return (indice_sobrecarga_calorica, clasificacion_isc, tiempo_exp_per, tiempo_de_recuperacion,evaporacion_max,evaporacion_req)

"""Función para calcular el tiempo en horas y minutos"""
#Función para mostrar el tiempo en formato horas y minutos
def format_time(minutes):
    if minutes == float('inf'):
        return "Sin límite (no hay estrés térmico)"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}h {m}min"

#Limpiar el pd dataframe
def sanitize_file(uploaded_file):
    # Determinar el tipo de archivo y cargarlo
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Formato de archivo no soportado")
    
    # Sanitizar el DataFrame
    sanitized_df = df.applymap(lambda x: f"'{x}" if isinstance(x, str) and x.startswith(('=', '@', '+', '-')) else x)
    return sanitized_df