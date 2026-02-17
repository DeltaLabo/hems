#Esteban Cañizales Jiménez
#2025-9-11
from math import sqrt

#Importar csv con datos de metabolismo, cavs y clo
lista_cavs= pd.read_csv("CAVS.csv")
lista_metabolismo= pd.read_csv("Metabolismo.csv")
lista_clo=pd.read_csv("Aislamiento.csv")

def fanger(temp_aire, humedad_relativa, velocidad_aire, temp_globo, seleccion_clo, carga_metabolica, peso, altura):

    iclo=lista_clo[lista_clo["Ropa de trabajo"]==seleccion_clo]["m²·K/W"].iloc[0]
    temp_radiante_media = temp_globo + 1.9 * sqrt(velocidad_aire) * (temp_globo - temp_aire)
    #Calculo del factor de superficie de la ropa fcl
    if iclo < 0.078:
        fcl = 1 + (1.29 * iclo) 
    else:
        fcl = 1.05 + (0.645 * iclo)
    #Cálculo de la temperatura de la superficie de la ropa en °C (tcl)
    tcl = 35.7-0.028 * (carga_metabolica-0)-iclo*(3.96*pow(10,-8)*fcl(((tcl))))