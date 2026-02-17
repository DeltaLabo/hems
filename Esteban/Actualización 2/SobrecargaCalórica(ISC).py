
##Este método es recomendado para exposiciones mayores a 30min y se recomienda utilizarlo en trabajadores jóvenes y sanos
##NORMA NTP 18: Estrés térmico. Evaluación de las exposiciones muy intensas
def indice_sobrecarga_calorica(carga_metabolica,velocidad_aire, temp_globo, temp_aire,presion_aire):
    # Solicitar al usuario la condición de vestimenta
    iclo = int(input("Indique la condición de vestimenta: \n culquier número para vestido o 0 para desnudo: "))
  
    # Definir los valores de K según la vestimenta
    if iclo != 0:#Condición vestido
        K_1, K_2, K_3 = 7, 4.4, 4.6
    elif iclo == 0:#Condición desnudo
        K_1, K_2, K_3 = 11.7, 7.3, 7.6
        exit()

    # Solicitar otros datos al usuario
    
    if velocidad_aire > 0.15:
            temp_radiante_media = ((((temp_globo + 273)**4) + (2.5 * (10**8)) * (velocidad_aire**0.6) * (temp_globo - temp_aire))**0.25) - 273
    else:
            temp_radiante_media = ((((temp_globo + 273)**4) + (0.42 * (10**8))*((temp_globo - temp_aire)**0.25)*(temp_globo - temp_aire))**0.25)- 273
    # Cálculo de los términos
    Smax=390 #Valor máximo de sudoración aceptado 390 W/m^2
    calor_rad = (K_2 * (temp_radiante_media - 35))
    calor_conv = (K_3 * (velocidad_aire ** 0.6) * (temp_aire - 35))
    Evaporacion_max = K_1 * (velocidad_aire** 0.6) * (56 - presion_aire)
    if Evaporacion_max > Smax: # Aquí se establece que si la evaporación máxima es superior a la sudoración máxima, el valor de evaporación se fija a 390 W/m^2
         Evaporacion_max=390
    Evaporacion_req = carga_metabolica + calor_rad + calor_conv  

    # Cálculo del Índice de Sobrecarga Calórica (ISC)
    indice_sobrecarga_calorica = (Evaporacion_req /Evaporacion_max) * 100
    print(f"El Índice de Sobrecarga Calórica (ISC) es: {indice_sobrecarga_calorica:.2f}%")

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
        Evaporacion_req=390
    elif indice_sobrecarga_calorica > 100:
        clasificacion_isc=("Condiciones críticas por sobrecarga calórica")
    tiempo_exp_per=(2440)/(Evaporacion_req-Evaporacion_max)
    print (f"El tiempo de exposición permitido es: {tiempo_exp_per:.2f}minutos")

    return (indice_sobrecarga_calorica,clasificacion_isc, tiempo_exp_per )


ISC,y, tiempo_exp_per = indice_sobrecarga_calorica(160,0.5,35,25,3.43)
