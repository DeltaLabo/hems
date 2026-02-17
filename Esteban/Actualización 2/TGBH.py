import pandas as pd
import math

def tgbh(radiacion_solar,temp_aire,temp_globo,temp_bulbo,cav,carga_metabolica,aclimatacion,capucha):
    
    if capucha == "Si":
        cavs+=1
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

