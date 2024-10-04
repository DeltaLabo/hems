import serial
import datetime
import csv
from matplotlib import pyplot as plt
from drawnow import drawnow


today = datetime.date.today().strftime('%Y-%m-%d')

# Create the filename using the date
filename = f"hems_{today}.csv"

def csv_write(filename):
    global lista
    with open(filename, "w+", newline="") as file:
        write = csv.writer(file)
        write.writerows(lista)
# Inicializa el serial
hems = serial.Serial('COM6',
                     baudrate=9600,
                     bytesize=8,
                     parity='N',
                     stopbits=1,
                     timeout=1.5
                     )

hems.close()
hems.open()
hems.flush()

time1 = []
time2 = []
temp1 = []
temp2 = []
pres1 = []
pres2 = []
humi1 = []
humi2 = []
lista = []

# plt.ion()     # tell matplotlib you want interactive mode to plot data
# fig = plt.figure()

def in_figure() -> None:

    plt.subplot(3,1,1)
    plt.plot(time1[-100:], temp1[-100:],label='globo')
    plt.plot(time2[-100:], temp2[-100:],label='bulbo')
    plt.legend()
    plt.title("SALES")
    plt.subplot(3,1,2)
    plt.plot(time1[-100:], humi1[-100:])
    plt.plot(time2[-100:], humi2[-100:])
    plt.subplot(3,1,3)
    plt.plot(time1[-100:], pres1[-100:])
    plt.plot(time2[-100:], pres2[-100:])
    


while True:
    line = hems.readline()

    if (line[:4].decode("utf-8") == str(datetime.date.today().year)):
        lista.append(line[:-2].decode("utf-8").split(sep=","))
        csv_write(filename)
        
        #print(line[:-2].decode("utf-8"))
        if lista[-1][1] == '1':
            time1.append(datetime.datetime.strptime(lista[-1][0], '%Y-%m-%d %H:%M:%S'))
            temp1.append(float(lista[-1][2]))
            pres1.append(float(lista[-1][3]))
            humi1.append(float(lista[-1][4]))
        
        if lista[-1][1] == '2':
            time2.append(datetime.datetime.strptime(lista[-1][0], '%Y-%m-%d %H:%M:%S'))
            temp2.append(float(lista[-1][2]))
            pres2.append(float(lista[-1][3]))
            humi2.append(float(lista[-1][4]))

        # print(line[:-2].decode("utf-8"))
        # lista.append([times.text, t1.text, t2.text, t3.text, t4.text, tavg.text, tref.text, draw_volt, draw_curr,capmeas, state])

    drawnow(in_figure)


    