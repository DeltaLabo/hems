from influxdb_client import InfluxDBClient, Point
import binascii

# --- Configuración InfluxDB ---
url = "https://us-east-1-1.aws.cloud2.influxdata.com"
token = "CL5c_fRaGa-qPdP3HNDL0u2SFKBb9JKAb_0qte8-fywJlGx3n7Ic9mY9rxh1i75wHaSobUY0tHiTRorKFzxvpQ=="
org = "HEMS"
bucket_src = "pruebas"
bucket_dst = "mediciones_decodificadas"

client = InfluxDBClient(url=url, token=token, org=org)
query_api = client.query_api()
write_api = client.write_api()

# --- Helpers ---
def get16(buf, pos):
    return (buf[pos] << 8) | buf[pos+1]

def get32(buf, pos):
    return (buf[pos] << 24) | (buf[pos+1] << 16) | (buf[pos+2] << 8) | buf[pos+3]

# --- Decodificación ---
def decode_frame(frame_hex):
    buf = bytearray(binascii.unhexlify(frame_hex))
    pos = 0

    print(f"\n--- Decodificando frame de {len(buf)} bytes ---")
    print("Hex completo:", frame_hex)

    if len(buf) < 38:
        raise ValueError(f"Frame demasiado corto: {len(buf)} bytes")
    
    if len(buf) > 40:
        raise ValueError(f"Frame demasiado corto: {len(buf)} bytes")

    if buf[pos] != 0xDD:
        raise ValueError("Start byte inválido")
    print(f"Start byte OK: {hex(buf[pos])}")
    pos += 1

    # Timestamp
    timestamp_ms = get32(buf, pos); pos += 4
    print(f"[{pos}] Timestamp={timestamp_ms}")

    # SHT1 y SHT2
    sht1T = get16(buf, pos) / 100.0; pos += 2
    print(f"[{pos}] SHT1 Temp={sht1T}")
    sht1RH = get16(buf, pos) / 100.0; pos += 2
    print(f"[{pos}] SHT1 RH={sht1RH}")
    sht2T = get16(buf, pos) / 100.0; pos += 2
    print(f"[{pos}] SHT2 Temp={sht2T}")
    sht2RH = get16(buf, pos) / 100.0; pos += 2
    print(f"[{pos}] SHT2 RH={sht2RH}")

    # UV
    uvA = get16(buf, pos) / 1000.0; pos += 2
    print(f"[{pos}] UV A={uvA}")
    uvB = get16(buf, pos) / 1000.0; pos += 2
    print(f"[{pos}] UV B={uvB}")
    uvC = get16(buf, pos) / 1000.0; pos += 2
    print(f"[{pos}] UV C={uvC}")

    # Entorno
    envT = get16(buf, pos) / 100.0; pos += 2
    print(f"[{pos}] Env Temp={envT}")
    envP_hPa = get16(buf, pos) / 10.0; pos += 2
    print(f"[{pos}] Env Pressure={envP_hPa}")
    envRH = get16(buf, pos) / 100.0; pos += 2
    print(f"[{pos}] Env RH={envRH}")

    # INA
    inaV = get16(buf, pos) / 100.0; pos += 2
    print(f"[{pos}] INA Voltage={inaV}")
    inaI = get16(buf, pos) / 10.0; pos += 2
    print(f"[{pos}] INA Current={inaI}")
    inaP = get16(buf, pos) / 10.0; pos += 2
    print(f"[{pos}] INA Power={inaP}")

    # Energía acumulada
    energy_mWh = get32(buf, pos) / 100.0; pos += 4
    print(f"[{pos}] Energy={energy_mWh}")

    # Flags
    overCurrent = buf[pos]; pos += 1
    print(f"[{pos}] OverCurrent={overCurrent}")
    okFlags = get16(buf, pos); pos += 2
    print(f"[{pos}] okFlags={okFlags}")

    # Verificación final
    print(f"Pos final={pos}, len={len(buf)}, último byte={hex(buf[-1])}")
    if buf[pos] != 0x77:
        raise ValueError("Stop byte inválido")

    return {
        "timestamp_ms": timestamp_ms,
        "sht1T": sht1T, "sht1RH": sht1RH,
        "sht2T": sht2T, "sht2RH": sht2RH,
        "uvA": uvA, "uvB": uvB, "uvC": uvC,
        "envT": envT, "envP_hPa": envP_hPa, "envRH": envRH,
        "inaV": inaV, "inaI": inaI, "inaP": inaP,
        "energy_mWh": energy_mWh,
        "overCurrent": overCurrent,
        "okFlags": okFlags
    }


# --- Flujo principal ---
query = f'from(bucket:"{bucket_src}") |> range(start: -30d) |> filter(fn: (r) => r["_field"] == "frame_hex")'
tables = query_api.query(query)

# Preguntar al usuario si desea guardar en InfluxDB
guardar = input("¿Desea guardar las mediciones decodificadas en InfluxDB? (s/n): ").strip().lower() == "s"

for table in tables:
    for record in table.records:
        frame_hex = record.get_value()
        buf = bytearray(binascii.unhexlify(frame_hex))

        # --- Depuración: mostrar longitud y últimos bytes ---
        print(f"Frame len={len(buf)} bytes, últimos 5 bytes: {[hex(b) for b in buf[-5:]]}")

        try:
            data = decode_frame(frame_hex)
            print("✅ Frame decodificado:", data)

            if guardar:
                p = Point("mediciones_decodificadas")
                for k,v in data.items():
                    p.field(k, v)
                write_api.write(bucket=bucket_dst, org=org, record=p)
        except Exception as e:
            print(f"⚠️ Frame inválido: {e}. Último byte real: {hex(buf[-1])}")

if guardar:
    print("Frames decodificados y escritos en bucket destino.")
else:
    print("Frames decodificados mostrados en consola, no se guardaron en InfluxDB.")
