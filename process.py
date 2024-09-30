import pandas as pd
from matplotlib import pyplot as plt

questTemp = pd.read_csv('questtemp_2024-09-25-17-09.csv')

print(questTemp.head())

questTemp = questTemp[questTemp['session'] == 1]

plt.figure()
plt.plot(questTemp.timestamp,questTemp.tgbhi)
plt.xticks(questTemp.timestamp[::10], rotation=45)  # Show every 10th label (adjust as necessary)
plt.tight_layout()  # Adjust layout
plt.show()