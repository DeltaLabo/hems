import serial
import pandas as pd
from datetime import datetime

today = datetime.today().strftime('%Y-%m-%d')

# Create the filename using the date
filename = f"{today}.csv"

questTemp = serial.Serial(port='COM12', baudrate=9600, bytesize=8,
                            parity='N', stopbits=1, timeout=1)


questTemp.close()
questTemp.open()
questTemp.flush()
counter = 0
data_list = []
line = ''
while(line != b'\x1a'):
    line = questTemp.readline()
    if line.startswith(b'\x0cSesion :') == True:
        sesion = int(line.decode("utf-8")[10])
        counter = 7

    if counter > 0:
        counter -= 1
        if counter == 0:
            while (not line.startswith(b'\x0c\r\n')):
                line = questTemp.readline()
                if not line.startswith(b'\x0c\r\n'):
                    values = line.decode("utf-8")[:-2].split("  ")
                    date_value = pd.to_datetime(values[0])  # Convert the first value to a date
                    int_values = [float(value) for value in values[1:]]  # Convert the rest to integers
                    values = [date_value] + int_values
                    values.insert(0,sesion)
                    data_list.append(values)

data = pd.DataFrame(data_list, columns=['session','timestamp','tgbhi','tgbhe','bh','bs','globo','hr','hdx'])

data.to_csv(filename,
            index=None)
print(data.head())
    
