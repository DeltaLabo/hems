import math
def indice_de_sudoracion(temp_aire, temp_globo, temp_bulbo, iclo, carga_metabolica, velocidad_aire, postura, aclimatacion):
    """Definición de constantes"""
    BOLTZMAN = 5.67 * (10**-8)  # W/((m²)(K**4))
    EMISIVIDAD_PIEL = 0.97
     # Diccionario de posturas y sus valores correspondientes
    postura_trabajo_dict = {
        "De pie": 0.77,
        "Sentado": 0.7,
        "Agachado": 0.67
    }
    
    postura_trabajo = postura_trabajo_dict[postura]

    # Cálculo de la temperatura radiante media
    if velocidad_aire > 0.15:
        temp_radiante_media = ((((temp_globo + 273)**4)  + (2.5 * (10**8)) * (velocidad_aire**0.6) * (temp_globo - temp_aire))**0.25) - 273
    else:
        temp_radiante_media = ((((temp_globo + 273)**4) + (0.42 * (10**8)) * ((temp_globo - temp_aire)**0.25) * (temp_globo - temp_aire))**0.25) - 273
    
    presion_saturacion_bulbo = math.exp(16.653 - (4030.18 / (temp_bulbo + 235)))  # (kPa)
    presion_parcial_ambiente = presion_saturacion_bulbo - 0.0667 * (temp_aire - temp_bulbo)  # (kPa)
    temp_piel = 30 + (0.0930 * temp_aire) + (0.045 * temp_radiante_media) - (0.571 * velocidad_aire) + (0.2540 * presion_parcial_ambiente) + (0.00128 * carga_metabolica) - (3.570 * iclo)

    presion_vapor_piel = math.exp(16.653 - (4030.18 / (temp_piel + 235)))
    
    # Calcular coeficientes y factores de reducción de la vestimenta
    velocidad_relativa_aire = velocidad_aire + (0.0052 * (carga_metabolica - 58))
    cambio_calor_conveccion = 3.5 + (5.2 * velocidad_relativa_aire)
    cambio_calor_radiacion = (EMISIVIDAD_PIEL * BOLTZMAN * postura_trabajo * (((temp_piel + 273)**4) - ((temp_radiante_media + 273)**4))) / (temp_piel - temp_radiante_media)
    cambio_calor_evaporacion = 16.7 * cambio_calor_conveccion
    fclo = 1 + (1.970 * iclo)
    f_mayus_clo = 1 / (((cambio_calor_conveccion + cambio_calor_radiacion) * iclo) + (1 / fclo))
    feclo = 1 / (1 + (2.22 * cambio_calor_conveccion * (iclo - ((fclo - 1) / ((cambio_calor_conveccion + cambio_calor_radiacion) * fclo)))))
    resistencia_total_vestido = 1 / (cambio_calor_evaporacion * feclo)

    # Calcular Emax
    evaporacion_maxima = (presion_vapor_piel - presion_parcial_ambiente) / resistencia_total_vestido
    
    # Cálculos de balance térmico
    conveccion_respiratoria = 0.0014 * carga_metabolica * (35 - temp_aire)
    evaporacion_respiratoria = 0.0173 * carga_metabolica * (5.624 - presion_parcial_ambiente)
    radiacion = cambio_calor_radiacion * f_mayus_clo * (temp_piel - temp_radiante_media)
    conveccion = cambio_calor_conveccion * f_mayus_clo * (temp_piel - temp_aire)
    evaporacion_requerida = carga_metabolica - conveccion_respiratoria - evaporacion_respiratoria - conveccion - radiacion
    
    # Análisis del puesto
    humedad_piel_predecida = evaporacion_requerida / evaporacion_maxima
    

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

    humedad_piel_maxima = aclimatacion_dict[aclimatacion]["w_max"]
    sudoracion_maxima = aclimatacion_dict[aclimatacion]["sw_max"]
    q_max_peligro = aclimatacion_dict[aclimatacion]["Q_max_peligro"]
    q_max_alarma = aclimatacion_dict[aclimatacion]["Q_max_alarma"]
    d_max_peligro = aclimatacion_dict[aclimatacion]["D_max_peligro"]
    d_max_alarma = aclimatacion_dict[aclimatacion]["D_max_alarma"]
    
    if humedad_piel_predecida > humedad_piel_maxima:
        humedad_piel_predecida = humedad_piel_maxima

    evaporacion_predecida = humedad_piel_predecida * evaporacion_maxima
    r_p = 1 - (humedad_piel_predecida**2) / 2
    sudoracion_predecida = evaporacion_predecida / r_p
    
    # Validar sudoracion_predecida contra sw_max
    if sudoracion_predecida > sudoracion_maxima:
        humedad_piel_predecida = math.sqrt((evaporacion_maxima / sudoracion_maxima)**2 + 2) - (evaporacion_maxima / sudoracion_maxima)
        evaporacion_predecida = humedad_piel_predecida * evaporacion_maxima
        sudoracion_predecida = sudoracion_maxima
   
    # Tiempos límite de exposición
    dle_alarma_q = 60 * q_max_alarma / (evaporacion_requerida - evaporacion_predecida)
    dle_peligro_q = 60 * q_max_peligro / (evaporacion_requerida - evaporacion_predecida)
    dle_alarma_d = 60 * d_max_alarma / sudoracion_predecida
    dle_peligro_d = 60 * d_max_peligro / sudoracion_predecida

    return dle_alarma_q, dle_peligro_q, dle_alarma_d, dle_peligro_d

