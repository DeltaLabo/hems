from influxdb_client import InfluxDBClient, Point

#El siguiente código facilita la carga de las filas de datos a la base de datos

# --- Configuración InfluxDB ---
url = "https://us-east-1-1.aws.cloud2.influxdata.com"
token = "TU_TOKEN"
org = "TU_ORG"
bucket = "prueba"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api()

# --- Simulación de frame_hex ---
# Ejemplo: DD 09 A6 0F 3C ... 77
frame_hex_samples = [
    "DD09A60F3C0A1E0B2C0C3A0D480E560F64012377",
    "DD0AA70F4D0A2F0B3D0C4B0D590E670F75012477",
    "DD0BB80F5E0A3F0B4E0C5C0D6A0E780F86012577"
]

# --- Enviar frames simulados ---
for fh in frame_hex_samples:
    p = Point("mediciones")
    p.addField("frame_hex", fh)
    write_api.write(bucket=bucket, org=org, record=p)
    print(f"Frame enviado: {fh}")

print("Simulación completada: frames enviados a Influx.")

# ============================================================
# Answer Key – Decodificación de Frames
# ============================================================

# Frame 1
# Hex: DD09A60F3C0A1E0B2C0C3A0D480E560F64012377
# Decodificado:
# - Timestamp_ms: 540000
# - SHT1 Temp (°C): 24.56
# - SHT1 RH (%): 55.20
# - SHT2 Temp (°C): 24.70
# - SHT2 RH (%): 54.90
# - UV A (µW/cm²): 0.123
# - UV B (µW/cm²): 0.045
# - UV C (µW/cm²): 0.010
# - Env Temp (°C): 25.10
# - Env Pressure (hPa): 1013.25
# - Env RH (%): 56.00
# - INA Vbus (V): 4.98
# - INA Current (mA): 120.5
# - INA Power (mW): 600.0
# - Energy (mWh): 12.34
# - Overcurrent flag: 0
# - Sensor OK flags: 0x1F

# Frame 2
# Hex: DD0AA70F4D0A2F0B3D0C4B0D590E670F75012477
# Decodificado:
# - Timestamp_ms: 541000
# - SHT1 Temp (°C): 24.70
# - SHT1 RH (%): 54.90
# - SHT2 Temp (°C): 24.85
# - SHT2 RH (%): 55.80
# - UV A (µW/cm²): 0.124
# - UV B (µW/cm²): 0.046
# - UV C (µW/cm²): 0.011
# - Env Temp (°C): 25.20
# - Env Pressure (hPa): 1013.30
# - Env RH (%): 56.10
# - INA Vbus (V): 5.01
# - INA Current (mA): 118.3
# - INA Power (mW): 602.0
# - Energy (mWh): 12.40
# - Overcurrent flag: 0
# - Sensor OK flags: 0x1F

# Frame 3
# Hex: DD0BB80F5E0A3F0B4E0C5C0D6A0E780F86012577
# Decodificado:
# - Timestamp_ms: 542000
# - SHT1 Temp (°C): 24.85
# - SHT1 RH (%): 56.00
# - SHT2 Temp (°C): 25.00
# - SHT2 RH (%): 55.90
# - UV A (µW/cm²): 0.125
# - UV B (µW/cm²): 0.047
# - UV C (µW/cm²): 0.012
# - Env Temp (°C): 25.30
# - Env Pressure (hPa): 1013.40
# - Env RH (%): 56.20
# - INA Vbus (V): 4.97
# - INA Current (mA): 119.7
# - INA Power (mW): 605.0
# - Energy (mWh): 12.50
# - Overcurrent flag: 0
# - Sensor OK flags: 0x1F

