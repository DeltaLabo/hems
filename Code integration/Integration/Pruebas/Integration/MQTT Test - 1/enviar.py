import paho.mqtt.client as mqtt
import time
import random

# Crear cliente MQTT
client = mqtt.Client()

# Conectar al broker Mosquitto (localhost si corre en tu PC)
client.connect("localhost", 1883, 60)

# Publicar mensajes en un bucle
for i in range(10):
    # Simulamos datos UV como ejemplo
    uvA = round(random.uniform(100, 200), 2)
    uvB = round(random.uniform(50, 100), 2)
    uvC = round(random.uniform(5, 20), 2)

    mensaje = f"UVA: {uvA} UVB: {uvB} UVC: {uvC}"
    client.publish("sensores/uv", mensaje)
    print(f"Publicado: {mensaje}")
    time.sleep(2)  # espera 2 segundos entre mensajes

client.disconnect()
