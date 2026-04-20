import paho.mqtt.client as mqtt

# Función que se ejecuta al recibir un mensaje
def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic} | Mensaje: {msg.payload.decode()}")

# Crear cliente MQTT
client = mqtt.Client()

# Asignar función de callback
client.on_message = on_message

# Conectar al broker Mosquitto en tu PC
# Si Mosquitto corre en la misma máquina: "localhost"
# Si corre en otra máquina: usa la IP de esa máquina
client.connect("localhost", 1883, 60)

# Suscribirse al tópico donde publica el ESP32
client.subscribe("sensores/uv")

# Mantener el cliente escuchando
print("Esperando mensajes MQTT...")
client.loop_forever()
