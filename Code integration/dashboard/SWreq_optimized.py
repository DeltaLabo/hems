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
    
    # Definición del Ar/Ad
    postura_trabajo = postura_trabajo_dict[postura]

    # Cálculo de la temperatura radiante media
    if velocidad_aire > 0.15:
        temp_radiante_media = (((temp_globo + 273)**4) + (2.5 * (10**8)) * (velocidad_aire**0.6) * (temp_globo - temp_aire))**0.25 - 273
    else:
        temp_radiante_media = (((temp_globo + 273)**4) + (2.5 * (10**8)) * ((temp_globo - temp_aire)**0.25) * (temp_globo - temp_aire))**0.25 - 273
    
    presion_saturacion_bulbo = math.exp(16.653 - (4030.18 / (temp_bulbo + 235)))  # (kPa)
    presion_parcial_ambiente = presion_saturacion_bulbo - 0.0667 * (temp_aire - temp_bulbo)  # (kPa)
    temp_piel = 30 + (0.0930 * temp_aire) + (0.045 * temp_radiante_media) - (0.571 * velocidad_aire) + (0.2540 * presion_parcial_ambiente) + (0.00128 * carga_metabolica) - (3.570 * iclo)

    presion_vapor_piel = math.exp(16.653 - (4030.18 / (temp_piel + 235)))
    
    # Calcular coeficientes y factores de reducción de la vestimenta
    var = velocidad_aire + (0.0052 * (carga_metabolica - 58))
    hc = 3.5 + (5.2 * var)
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
    print(e_p,e_req,sw_p)
    # Tiempos límite de exposición
    dle_alarma_q = 60 * q_max_alarma / (e_req - e_p)
    dle_peligro_q = 60 * q_max_peligro / (e_req - e_p)
    dle_alarma_d = 60 * d_max_alarma / sw_p
    dle_peligro_d = 60 * d_max_peligro / sw_p

    return dle_alarma_q, dle_peligro_q, dle_alarma_d, dle_peligro_d

