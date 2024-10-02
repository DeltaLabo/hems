import pandas as pd
from matplotlib import pyplot as plt

hems = pd.read_csv('tests/hems_2.0.csv',names=['timestamp','sens','temp','pres','humi'],parse_dates=['timestamp'], infer_datetime_format=True)
quest = pd.read_csv('tests/quest_2.0.csv',parse_dates=['timestamp'], infer_datetime_format=True)

print(hems.head())

hems1 = hems[hems['timestamp'].isin(quest['timestamp'])]\
        [hems['sens']==1]\
        .reset_index(drop=True).drop('sens',axis=1)

hems2 = hems[hems['timestamp'].isin(quest['timestamp'])]\
        [hems['sens']==2]\
        .reset_index(drop=True).drop('sens',axis=1)

quest = quest[quest['timestamp'].isin(hems1['timestamp'])]\
        .reset_index(drop=True)


plt.figure()
plt.plot(hems1.timestamp,hems1.temp,label='hems1')
plt.plot(hems2.timestamp,hems2.temp,label='hems2')
plt.xticks(rotation=45)
plt.plot(quest.timestamp,quest.globo,label='questglobo')
plt.legend()
plt.show()

plt.figure()
plt.plot(hems1.timestamp,hems1.humi,label='hems1')
plt.plot(hems2.timestamp,hems2.humi,label='hems2')
plt.xticks(rotation=45)
plt.plot(quest.timestamp,quest.hr,label='quest')
plt.legend()
plt.show()