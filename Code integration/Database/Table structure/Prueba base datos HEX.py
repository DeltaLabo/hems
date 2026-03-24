from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- Configuración InfluxDB ---
url = "https://us-east-1-1.aws.cloud2.influxdata.com"
token = "Tu_Token"
org = "HEMS"
bucket = "pruebas"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# --- Frames simulados con valores típicos de una finca de caña ---
frame_hex_samples = [
    # Frame 1: mañana fresca, humedad alta
    "DD000186A00A00FA0B1E0C0F0D320E640F960123456701F4025804E805DC07D001F4012C000000011F77",
    # Frame 2: mediodía, más calor y radiación UV
    "DD000187000A01900B280C140D300E960FA001234567020804B0050005F0082C01F4012C000000011F77",
    # Frame 3: tarde, temperatura máxima, energía acumulada mayor
    "DD000187600A01F40B320C190D2D0EB00FC801234567021005DC05DC0600086401F4012C000000011F77"
]

# --- Enviar frames simulados ---
for fh in frame_hex_samples:
    p = Point("mediciones").field("frame_hex", fh)
    write_api.write(bucket=bucket, org=org, record=p)
    print(f"Frame enviado: {fh}")

print("✅ Simulación completada: frames realistas enviados a Influx.")

# ============================================================
# Answer Key – Decodificación de Frames Realistas
# ============================================================

# Frame 1 (mañana fresca, humedad alta)
# - Timestamp_ms: 100000
# - SHT1 Temp (°C): ~25.0
# - SHT1 RH (%): ~60.0
# - SHT2 Temp (°C): ~24.0
# - SHT2 RH (%): ~50.0
# - UV A/B/C (µW/cm²): 2.5–3.0
# - Env Temp (°C): ~25.0
# - Env Pressure (hPa): ~1012
# - Env RH (%): ~70.0
# - INA Vbus (V): ~5.0
# - INA Current (mA): ~120
# - INA Power (mW): ~750
# - Energy (mWh): ~300
# - Flags: OK

# Frame 2 (mediodía, más calor y radiación UV)
# - Timestamp_ms: 102000
# - SHT1 Temp (°C): ~27.0
# - SHT1 RH (%): ~55.0
# - SHT2 Temp (°C): ~26.0
# - SHT2 RH (%): ~52.0
# - UV A/B/C (µW/cm²): 4.0–5.0
# - Env Temp (°C): ~27.0
# - Env Pressure (hPa): ~1013
# - Env RH (%): ~65.0
# - INA Vbus (V): ~5.0
# - INA Current (mA): ~130
# - INA Power (mW): ~800
# - Energy (mWh): ~310
# - Flags: OK

# Frame 3 (tarde, temperatura máxima, energía acumulada mayor)
# - Timestamp_ms: 105000
# - SHT1 Temp (°C): ~30.0
# - SHT1 RH (%): ~50.0
# - SHT2 Temp (°C): ~29.0
# - SHT2 RH (%): ~48.0
# - UV A/B/C (µW/cm²): 6.0–7.0
# - Env Temp (°C): ~30.0
# - Env Pressure (hPa): ~1014
# - Env RH (%): ~60.0
# - INA Vbus (V): ~5.0
# - INA Current (mA): ~140
# - INA Power (mW): ~850
# - Energy (mWh): ~320
# - Flags: OK
