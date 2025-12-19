from flask import Flask, jsonify
import pandas as pd
import random
import time
from threading import Thread, Lock
import atexit

app = Flask(__name__)

# Variables compartidas con protección de hilos
df = pd.DataFrame(columns=["Temperatura seca", "Temperatura humeda", 
                          "Temperatura de globo", "Velocidad del aire"])
lock = Lock()
detener_hilo = False

def generar_datos():
    global df, detener_hilo
    while not detener_hilo:
        # Generar nuevos datos
        temp_humeda = round(random.uniform(18, 32), 1)
        temp_seca = round(random.uniform(temp_humeda, 35), 1)
        temp_globo = round(random.uniform(temp_seca, 38), 1)
        velocidad_aire = round(random.uniform(0.1, 0.7), 1)
        
        nuevos_datos = {
            "Temperatura seca": temp_seca,
            "Temperatura humeda": temp_humeda,
            "Temperatura de globo": temp_globo,
            "Velocidad del aire": velocidad_aire
        }
        
        # Añadir datos al DataFrame con protección de hilo
        with lock:
            df = pd.concat([df, pd.DataFrame([nuevos_datos])], ignore_index=True)
        
        time.sleep(1)

@app.route('/')
def home():
    return "Sistema de monitoreo ambiental - Accede a /datos para ver las mediciones"

@app.route('/datos')
def obtener_datos():
    with lock:
        # Convertir últimos 10 registros a formato JSON
        datos = df.to_dict(orient='records')
    return jsonify(datos)

@app.route('/ultima-medicion')
def ultima_medicion():
    with lock:
        if df.empty:
            return jsonify({"mensaje": "Aún no hay datos registrados"})
        ultima = df.iloc[-1].to_dict()
    return jsonify(ultima)

def detener_generador():
    global detener_hilo
    detener_hilo = True

if __name__ == '__main__':
    # Iniciar hilo generador de datos
    hilo_generador = Thread(target=generar_datos)
    hilo_generador.daemon = True
    hilo_generador.start()
    
    # Registrar función de limpieza al salir
    atexit.register(detener_generador)
    
    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=False)