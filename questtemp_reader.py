import serial
import pandas as pd
from datetime import datetime
from matplotlib import pyplot as plt

today = datetime.today().strftime('%Y-%m-%d')

# Create the filename using the date
filename = f"questtemp_{today}.csv"

source = input("(a)rchivo o (s)erial?")

if (source == "a"):
    questTemp = open('text_file.txt','r')
elif (source == 's'):
    questTemp = serial.Serial(port='COM4', baudrate=9600, bytesize=8,
                            parity='N', stopbits=1, timeout=1)

if (source == 's'):
    questTemp.close()
    questTemp.open()
    questTemp.flush()

counter = 0
data_list = []
line = ''
EOFf = False

while(EOFf == False):
    if (source == 's'):
        line = questTemp.readline().decode('ascii')
    elif (source == 'a'):
        line = questTemp.readline()

    print(line[:-1])

    if line[:-1].endswith('Pagina 1'):
        counter = 33

    if line.endswith('\x1a'):
        EOFf = True

    if line.startswith('\x0cSesion :') == True:
        sesion = int(line[10])
        counter = 8

    if counter > 0:
        counter -= 1
    
    if counter == 0:
        if (not line[:-1].endswith('\x0c')):
            values = line[:-2].split("  ")
            date_value = pd.to_datetime(values[0])  # Convert the first value to a date
            int_values = [float(value) for value in values[1:]]  # Convert the rest to integers
            values = [date_value] + int_values
            values.insert(0,sesion)
            data_list.append(values)


data = pd.DataFrame(data_list, columns=['session','timestamp','tgbhi','tgbhe','bh','bs','globo','hr','hdx'])

data.to_csv(filename,
            index=None)
print(data.head())

data = data[data['session'] == 1]

plt.figure()
plt.plot(data.timestamp, data.hr)
plt.show()
