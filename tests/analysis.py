import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error

hems = pd.read_csv('tests/hems_5.0.csv',names=['timestamp','sens','temp','pres','humi'],parse_dates=['timestamp'], infer_datetime_format=True)
quest = pd.read_csv('tests/quest_5.0.csv',parse_dates=['timestamp'], infer_datetime_format=True)

print(hems.head())

hems1 = hems[hems['timestamp'].isin(quest['timestamp'])]\
        [hems['sens']==1]\
        .reset_index(drop=True).drop('sens',axis=1)

hems2 = hems[hems['timestamp'].isin(quest['timestamp'])]\
        [hems['sens']==2]\
        .reset_index(drop=True).drop('sens',axis=1)

quest = quest[quest['timestamp'].isin(hems1['timestamp'])]\
        .reset_index(drop=True)

print(hems1.columns)
print(hems2.columns)
print(quest.columns)
def calculate_rmse(actual, predicted):
    return np.sqrt(mean_squared_error(actual, predicted))

# Calcular el RMSE como porcentaje
def calculate_rmse_percentage(actual, predicted):
    rmse = calculate_rmse(actual, predicted)
    return (rmse / np.mean(actual)) * 100  # RMSE en porcentaje

columns_mapping = {
    'temp': 'globo',   
    'humi': 'hr'       
}
rmse_results = {}
for hems_column, quest_column in columns_mapping.items():
    real_values = quest[quest_column]  
    predicted_values = hems1[hems_column]  
    rmse_percentage = calculate_rmse_percentage(real_values, predicted_values)
    rmse_results[f'hems1 vs quest ({hems_column})'] = rmse_percentage

for hems_column, quest_column in columns_mapping.items():
    real_values = quest[quest_column]  
    predicted_values = hems2[hems_column]  
    rmse_percentage = calculate_rmse_percentage(real_values, predicted_values)
    rmse_results[f'hems2 vs quest ({hems_column})'] = rmse_percentage

# Mostrar los resultados en porcentaje
for comparison, rmse_percentage in rmse_results.items():
    print(f'RMSE Percentage for {comparison}: {rmse_percentage:.2f}%')

plt.figure()
hems1['temp'] = 1.04*hems1['temp'] - 1
plt.plot(hems1.timestamp,hems1.temp,label='hems/globo')
#plt.plot(hems2.timestamp,hems2.temp,label='hems/bulbo')
plt.xticks(rotation=45)
plt.plot(quest.timestamp,quest.globo,label='questglobo')
plt.title('Prueba al vacío: Prototipo vs Questtemp')  
plt.xlabel('Tiempo') 
plt.ylabel('Temperatura de globo (°C)') 
plt.legend()
plt.show()

plt.figure()
#plt.plot(hems1.timestamp,hems1.humi,label='hems/globo')
plt.plot(hems2.timestamp,hems2.humi,label='hems/bulbo')
plt.xticks(rotation=45)
plt.plot(quest.timestamp,quest.hr,label='quest')
plt.title('Comparación de temperatura de bulbo')  
plt.xlabel('Tiempo')  
plt.ylabel('Humedad relativa (%)')  
plt.legend()
plt.show()