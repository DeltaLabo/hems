import serial
import pandas as pd
import time
from datetime import datetime
from matplotlib import pyplot as plt

today = datetime.today().strftime('%Y-%m-%d-%H-%M')

in_filename = 'text_file.txt'

out_filename = f"quest_{today}.csv"

source = input("(a)rchivo o (s)erial?")

if (source == "a"):
    questTemp = open(in_filename,'r')
    end_of_line = -1
elif (source == 's'):
    questTemp = serial.Serial(port='COM4', baudrate=9600, bytesize=8,
                            parity='N', stopbits=1, timeout=1)
    end_of_line = -2

if (source == 's'):
    questTemp.close()
    questTemp.open()
    questTemp.flush()
    while(questTemp.in_waiting == 0):
        print('Wating for serial...')
        time.sleep(1)

counter = 0
data_list = []
line = ''
EOFf = False

while(EOFf == False):
    if (source == 's'):
        line = questTemp.readline().decode('ascii')
    elif (source == 'a'):
        line = questTemp.readline()

    if counter > 0:
        counter -= 1

    if line[:end_of_line].endswith('Pagina 1'):
        counter = 32

    if line.endswith('\x1a'):
        EOFf = True

    if line.startswith('\x0cSesion :') == True:
        sesion = int(line[10])
        counter = 7

    if counter == 0:
        if (not line[:end_of_line].endswith('\x0c')):
            print(line[:-2])
            values = line[:-2].split("  ")
            date_value = pd.to_datetime(values[0])  # Convert the first value to a date
            int_values = [float(value) for value in values[1:]]  # Convert the rest to integers
            values = [date_value] + int_values
            values.insert(0,sesion)
            data_list.append(values)


data = pd.DataFrame(data_list, columns=['session','timestamp','tgbhi','tgbhe','bh','bs','globo','hr','hdx'])

data.to_csv(out_filename,
            index=None)

print(data.head(50))

data = data[data['session'] == 1]

plt.figure()
plt.plot(data.timestamp, data.hr)
plt.show()
