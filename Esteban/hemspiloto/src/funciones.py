import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

"""Función para el cálculo del índice de calor"""

def indice_de_calor(temp_aire, humedad_relativa,exposicion_solar):
    temp_aire= temp_aire * 9/5 + 32  # Convertir a Fahrenheit
    indice_preliminar= 0.5*(temp_aire+61.0+((temp_aire-68)*1.2)+(humedad_relativa*0.094))
    
    medidas = {
        "Nivel I": [
            "Asegurar la disponibilidad de agua potable durante toda la jornada.",
            "Proporcionar áreas de sombra (semi o permanentes) para descanso en campo abierto.",
            "Proporcionar sombrero de ala ancha o gorra con cubre-cuello, mangas largas y usar protector solar cuando sea posible.",
            "Capacitar a los trabajadores.",
            "Cuando los trabajadores requieren el uso de prendas pesadas (CLO +1, +2), capas o uniformes no transpirables/impermeables, aplicar las medidas del nivel III.",
            "Las personas que sean nuevas o que retornen al trabajo deben aclimatarse",
            "Designar a una persona que esté capacitada sobre las manifestaciones clínicas relacionadas con la sobrecarga térmica y que sea capaz de informar a este respecto a la persona con la autoridad requerida y con la persona encargada de salud ocupacional para modificar las actividades laborales y el horario de trabajo/descanso como se requiera"
        ],
        "Nivel II": [
            "Asegurar la disponibilidad de agua potable durante toda la jornada.",
            "Proporcionar áreas de sombra (semi o permanentes) para descanso en campo abierto.",
            "Proporcionar sombrero de ala ancha o gorra con cubre-cuello, mangas largas y usar protector solar cuando sea posible.",
            "Capacitar a los trabajadores.",
            "Cuando los trabajadores requieren el uso de prendas pesadas (CLO +1, +2), capas o uniformes no transpirables/impermeables, aplicar las medidas del nivel III.",
            "Las personas que sean nuevas o que retornen al trabajo deben aclimatarse",
            "Designar a una persona que esté capacitada sobre las manifestaciones clínicas relacionadas con la sobrecarga térmica y que sea capaz de informar a este respecto a la persona con la autoridad requerida y con la persona encargada de salud ocupacional para modificar las actividades laborales y el horario de trabajo/descanso como se requiera"
        ],
        "Nivel III": [
            "Asegurar la disponibilidad de agua potable durante toda la jornada.",
            "Proporcionar áreas de sombra (semi o permanentes) para descanso en campo abierto.",
            "Proporcionar sombrero de ala ancha o gorra con cubre-cuello, mangas largas y usar protector solar cuando sea posible.",
            "Capacitar a los trabajadores.",
            "Las personas que sean nuevas o que retornen al trabajo deben aclimatarse",
            "Designar a una persona que esté capacitada sobre las manifestaciones clínicas relacionadas con la sobrecarga térmica y que sea capaz de informar a este respecto a la persona con la autoridad requerida y con la persona encargada de salud ocupacional para modificar las actividades laborales y el horario de trabajo/descanso como se requiera",
            "Establecer y cumplir horarios de trabajo/descanso.",
            "Informar a las personas trabajadoras sobre el horario establecido.",
            "Si el trabajo se realiza directamente bajo el sol, aplicar las medidas específicas del nivel IV descritas para esa condición."
        ],
        "Nivel IV": [
            "Asegurar la disponibilidad de agua potable durante toda la jornada.",
            "Suministrar bebidas rehidratantes según normativa del Ministerio de Salud.",
            "Proporcionar áreas de sombra (semi o permanentes) para descanso en campo abierto.",
            "Proporcionar sombrero de ala ancha o gorra con cubre-cuello, mangas largas y usar protector solar cuando sea posible.",
            "Capacitar a los trabajadores.",
            "Las personas que sean nuevas o que retornen al trabajo deben aclimatarse",
            "Designar a una persona que esté capacitada sobre las manifestaciones clínicas relacionadas con la sobrecarga térmica y que sea capaz de informar a este respecto a la persona con la autoridad requerida y con la persona encargada de salud ocupacional para modificar las actividades laborales y el horario de trabajo/descanso como se requiera",
            "Establecer y cumplir horarios de trabajo/descanso.",
            "Informar a las personas trabajadoras sobre el horario establecido.",
        ],
    }
    
    if indice_preliminar >= 80:
        ih =-42.379 + 2.04901523*temp_aire + 10.14333127*humedad_relativa - .22475541*temp_aire*humedad_relativa - .00683783*temp_aire*temp_aire - .05481717*humedad_relativa*humedad_relativa + .00122874*temp_aire*temp_aire*humedad_relativa + .00085282*temp_aire*humedad_relativa*humedad_relativa - .00000199*temp_aire*temp_aire*humedad_relativa*humedad_relativa
        #Ajuste 1. Si la humedad relativa es menor al 13% y la temperatura del aire está entre 80°F y 112°F se resta el ajuste
        if (humedad_relativa <13) and (80 < temp_aire <112):
            ajuste= ((13-humedad_relativa)/4)*math.sqrt((17-abs(temp_aire-95))/17)
            ih=ih-ajuste
        #Ajuste 2. Si la humedad relativa es mayor al 85% y la temperatura del aire está entre 80°F y 87°F se suma el ajuste
        if (80 < temp_aire <87) and (humedad_relativa > 85):
            ajuste= ((humedad_relativa-85)/10) * ((87-temp_aire)/5)
            ih=ih+ajuste
    else:
        ih=indice_preliminar
    if ih <91:
        nivel="Nivel I"
        efecto= "Es posible que tenga fatiga con exposiciones prolongadas y actividad física."
        if exposicion_solar == "Si":
            nivel_para_medidas="Nivel II"
            medidas_por_nivel = medidas[nivel_para_medidas]
        else:
            nivel_para_medidas="Nivel I"
            medidas_por_nivel = medidas[nivel]
        return (ih, nivel, efecto, medidas_por_nivel,nivel_para_medidas)
    elif 91<= ih <103:
        nivel="Nivel II"
        efecto="Posible insolación, calambres y agotamiento por exposición prolongada y actividad física"
        if exposicion_solar == "Si":
            nivel_para_medidas="Nivel III"
            medidas_por_nivel = medidas[nivel_para_medidas]
        else:
            nivel_para_medidas="Nivel II"
            medidas_por_nivel = medidas[nivel]
        return (ih, nivel, efecto, medidas_por_nivel, nivel_para_medidas)
    elif 103<= ih <125:
        nivel="Nivel III"
        efecto= "Probable insolación, calambres y agotamiento por exposición prolongada y actividad física"
        if exposicion_solar == "Si":
            nivel_para_medidas="Nivel IV"
            medidas_por_nivel = medidas[nivel_para_medidas]
        else:
            nivel_para_medidas="Nivel III"
            medidas_por_nivel = medidas[nivel]
        return (ih, nivel, efecto, medidas_por_nivel,nivel_para_medidas)
    elif ih >=125:        
        nivel="Nivel IV"
        efecto= "Probabilidad alta de insolación, golpe de calor "
        medidas_por_nivel = medidas[nivel]
        nivel_para_medidas = "Nivel IV"
        return (ih, nivel, efecto, medidas_por_nivel, nivel_para_medidas)
    
        


"""Función para el cálculo del índice de sudoracion requerida (SWreq)"""

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
    if e_max < 0:
        return (0,0,0,0)
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

        # Clasificación según la nueva escala
    if indice_sobrecarga_calorica <= 10:
        clasificacion_isc = "Confort térmico"
    elif indice_sobrecarga_calorica <= 30:
        clasificacion_isc = "Carga suave"
    elif indice_sobrecarga_calorica <= 40:
        clasificacion_isc = "Carga moderada (Zona de alarma)"
    elif indice_sobrecarga_calorica <= 80:
        clasificacion_isc = "Carga severa"
    elif indice_sobrecarga_calorica < 100:
        clasificacion_isc = "Carga muy severa"
    elif indice_sobrecarga_calorica == 100:
        clasificacion_isc = "Carga máxima permisible"
    else:
        clasificacion_isc = "Condiciones críticas por sobrecarga calórica"

    # Cálculo del tiempo de exposición permitido
    if indice_sobrecarga_calorica > 100:
        tiempo_exp_per = 2440 / (evaporacion_req - evaporacion_max)
    else:
        tiempo_exp_per = float('inf')
    
    #Tiempo de recuperación Programable posteriormente ya que requiere de las condiciones de la zona de descanso
    #superficie_corporal=(peso**0.425)*(altura**0.725)*0.007184
    #tiempo_de_recuperacion= (58+peso*1)/((evaporacion_max-evaporacion_req)*superficie_corporal) #minutos
    
    return (indice_sobrecarga_calorica, clasificacion_isc, tiempo_exp_per, evaporacion_max, evaporacion_req)

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

def redondear_velocidad(velocidad_aire):
    if velocidad_aire <= 0.075:
        return 0.05
    elif velocidad_aire <= 0.125:
        return 0.10
    elif velocidad_aire <= 0.175:
        return 0.15
    elif velocidad_aire <= 0.25:
        return 0.20

    elif velocidad_aire <= 0.35:
        return 0.30

    elif velocidad_aire <= 0.45:
        return 0.40

    elif velocidad_aire <= 0.75:
        return 0.50

    elif velocidad_aire <= 1.25:
        return 1.00

    else:
        return 1.50

#Función para Fanger (Confort térmico)
def Fanger (carga_metabolica,velocidad_aire, temp_globo, temp_aire,temp_bulbo,humedad_relativa,iclo):
 carga_metabolica=carga_metabolica/1.7
 actividad= "Ninguna"
 if 58<=carga_metabolica<87:
        actividad="Sedentaria"
 elif 87<=carga_metabolica<145:
        actividad="Media"
 elif 145<=carga_metabolica<232:
        actividad="Alta"
 trabajo=0

 #Cálculo temperatura radiante media
 if velocidad_aire > 0.15:
            temp_radiante_media = ((((temp_globo + 273)**4) + (2.5 * (10**8)) * (velocidad_aire**0.6) * (temp_globo - temp_aire))**0.25) - 273
 else:
            temp_radiante_media = ((((temp_globo + 273)**4) + (0.42 * (10**8))*((temp_globo - temp_aire)**0.25)*(temp_globo - temp_aire))**0.25)- 273
    
 # Cálculo de los términos
 presion_saturacion_bulbo = math.exp(16.653 - (4030.18 / (temp_bulbo + 235)))  # (kPa)
 presion_parcial_ambiente = (presion_saturacion_bulbo - 0.0667 * (temp_aire - temp_bulbo))  # kPa actualmente(kPa o hPa) preguntar a Adrian por esto
 velocidad_aire_relativa = velocidad_aire + (0.0052 * (carga_metabolica - 58))

#Flujo de calor sensible de la piel hacia el exterior del vestido
 K=((carga_metabolica-trabajo)-3.05*(5.766-0.00704*(carga_metabolica-trabajo)-presion_parcial_ambiente)-0.42*(carga_metabolica-trabajo-58.15)-0.0172*carga_metabolica*(5.867-presion_parcial_ambiente)-0.0014*carga_metabolica*(34-temp_aire))
 
 #Factor iclo Fanger
 if iclo<0.078:
        fclo= 1+1.29*iclo
 else:
        fclo= 1.05+0.65*iclo

 tclo= 35.7-0.0275*(carga_metabolica-trabajo)-iclo*K

 #Coeficientes de convección Fanger
 hc1= 2.38*(tclo-temp_aire)**0.25
 hc2= 12.1*(velocidad_aire_relativa)**0.5
 hc=max(hc1, hc2)

 temp_pielF = 35.7-0.0275*(carga_metabolica-trabajo)


 #Expresiones ecuación balance térmico
 perdida_ev_sudor=0.42*(carga_metabolica-trabajo-58.15)
 perdida_difusion=3.05*(0.256*temp_pielF-3.373-presion_parcial_ambiente)
 conveccion_resp= 0.0014*carga_metabolica*(34-temp_aire)
 evaporación_res= 0.0172*carga_metabolica*(5.867-presion_parcial_ambiente)
 perdida_radiacion=3.95*10**(-8)*fclo(((tclo+273)**4)-((temp_radiante_media+273)**4))
 perdida_conveccion=fclo*hc*(tclo-temp_aire)

#TABLAS
#Importar las tablas de factores de corrección por humedad y temperatura radiante media
 lista_fh_sedentaria = pd.read_csv("factores_de_correccion_humedad_sedentaria.csv")
 lista_fh_media = pd.read_csv("factores_de_correccion_humedad_media.csv")
 lista_fh_alta = pd.read_csv("factores_de_correccion_humedad_alta.csv")
 lista_fr_sedentaria = pd.read_csv("factores_de_correccion_trm_sedentaria.csv")
 lista_fr_media = pd.read_csv("factores_de_correccion_trm_media.csv")
 lista_fr_alta = pd.read_csv("factores_de_correccion_trm_alta.csv")

#Acomodar tablas
 lista_fh_sedentaria.rename(columns={lista_fh_sedentaria.columns[0]: "velocidad_aire"}, inplace=True)
 lista_fh_sedentaria["velocidad_aire"] = pd.to_numeric(lista_fh_sedentaria["velocidad_aire"])
 lista_fh_sedentaria.columns = ["velocidad_aire"] + [float(col) for col in lista_fh_sedentaria.columns[1:]]
 lista_fh_sedentaria.set_index("velocidad_aire", inplace=True)

 lista_fh_media.rename(columns={lista_fh_media.columns[0]: "velocidad_aire"}, inplace=True)
 lista_fh_media["velocidad_aire"] = pd.to_numeric(lista_fh_media["velocidad_aire"])
 lista_fh_media.columns = ["velocidad_aire"] + [float(col) for col in lista_fh_media.columns[1:]]
 lista_fh_media.set_index("velocidad_aire", inplace=True)

 lista_fh_alta.rename(columns={lista_fh_alta.columns[0]: "velocidad_aire"}, inplace=True)
 lista_fh_alta["velocidad_aire"] = pd.to_numeric(lista_fh_alta["velocidad_aire"])
 lista_fh_alta.columns = ["velocidad_aire"] + [float(col) for col in lista_fh_alta.columns[1:]]
 lista_fh_alta.set_index("velocidad_aire", inplace=True)

 lista_fr_sedentaria.rename(columns={lista_fr_sedentaria.columns[0]: "velocidad_aire"}, inplace=True)
 lista_fr_sedentaria["velocidad_aire"] = pd.to_numeric(lista_fr_sedentaria["velocidad_aire"])
 lista_fr_sedentaria.columns = ["velocidad_aire"] + [float(col) for col in lista_fr_sedentaria.columns[1:]]
 lista_fr_sedentaria.set_index("velocidad_aire", inplace=True)

 lista_fr_media.rename(columns={lista_fr_media.columns[0]: "velocidad_aire"}, inplace=True)
 lista_fr_media["velocidad_aire"] = pd.to_numeric(lista_fr_media["velocidad_aire"])
 lista_fr_media.columns = ["velocidad_aire"] + [float(col) for col in lista_fr_media.columns[1:]]
 lista_fr_media.set_index("velocidad_aire", inplace=True)

 lista_fr_alta.rename(columns={lista_fr_alta.columns[0]: "velocidad_aire"}, inplace=True)
 lista_fr_alta["velocidad_aire"] = pd.to_numeric(lista_fr_alta["velocidad_aire"])
 lista_fr_alta.columns = ["velocidad_aire"] + [float(col) for col in lista_fr_alta .columns[1:]]
 lista_fr_alta.set_index("velocidad_aire", inplace=True)

 #Selección de los la tabla de factores de corrección
 if actividad == "Sedentaria":
    tabla_fh = lista_fh_sedentaria
    tabla_fr = lista_fr_sedentaria
 elif actividad == "Media":
    tabla_fh = lista_fh_media
    tabla_fr = lista_fr_media
 elif actividad== "Alta":
    tabla_fh = lista_fh_alta
    tabla_fr = lista_fr_alta

 velocidad_ivm=redondear_velocidad(velocidad_aire)
#Selección del factor de corrección
 factor_humedad = tabla_fh.loc[velocidad_ivm, iclo]
 factor_radiacion = tabla_fr.loc[velocidad_ivm, iclo]

#Indice de valoración medio
 indice_valoracion_medio=(0.303*math.exp(-0.036*carga_metabolica)+0.028)*(carga_metabolica-trabajo-perdida_ev_sudor-perdida_difusion-conveccion_resp-evaporación_res-perdida_radiacion-perdida_conveccion)
 indice_valoracion_medio_final= indice_valoracion_medio+factor_humedad*(humedad_relativa-50)+factor_radiacion*(temp_radiante_media-temp_aire)
 
 #Porcentaje de personas insatisfechas
 porcentaje_insatisfechos=100-95* math.exp(-0.03353*(indice_valoracion_medio_final**4)-0.2179*indice_valoracion_medio_final**2)
 return (indice_valoracion_medio_final, porcentaje_insatisfechos)
