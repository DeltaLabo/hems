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

def show_val(name, buf, pos, length, scale=1.0, unit=""):
    # Extrae los bytes en hex
    hex_str = "".join(f"{b:02X}" for b in buf[pos:pos+length])
    # Convierte a entero según longitud
    if length == 2:
        val = get16(buf, pos)
    elif length == 4:
        val = get32(buf, pos)
    else:
        val = buf[pos]
    # Aplica escala si corresponde
    val_scaled = val / scale if scale != 1.0 else val
    print(f"{name}: hex={hex_str}, int={val}, valor={val_scaled}{unit}")
    return val_scaled

def decode_frame(frame_hex):
    buf = bytearray(binascii.unhexlify(frame_hex))
    pos = 0

    if len(buf) != 39:
        raise ValueError(f"Frame inválido: longitud {len(buf)} bytes, se esperaban 39")

    if buf[pos] != 0xDD:
        raise ValueError("Start byte inválido")
    print(f"Start byte: {hex(buf[pos])}")
    pos += 1

    # Timestamp
    timestamp_ms = show_val("Timestamp_ms", buf, pos, 4); pos += 4

    # SHT1 y SHT2
    sht1T = show_val("SHT1 Temp", buf, pos, 2, scale=100.0, unit=" °C"); pos += 2
    sht1RH = show_val("SHT1 RH", buf, pos, 2, scale=100.0, unit=" %"); pos += 2
    sht2T = show_val("SHT2 Temp", buf, pos, 2, scale=100.0, unit=" °C"); pos += 2
    sht2RH = show_val("SHT2 RH", buf, pos, 2, scale=100.0, unit=" %"); pos += 2

    # UV
    uvA = show_val("UV A", buf, pos, 2, scale=1000.0); pos += 2
    uvB = show_val("UV B", buf, pos, 2, scale=1000.0); pos += 2
    uvC = show_val("UV C", buf, pos, 2, scale=1000.0); pos += 2

    # Entorno
    envT = show_val("Env Temp", buf, pos, 2, scale=100.0, unit=" °C"); pos += 2
    envP_hPa = show_val("Env Pressure", buf, pos, 2, scale=10.0, unit=" hPa"); pos += 2
    envRH = show_val("Env RH", buf, pos, 2, scale=100.0, unit=" %"); pos += 2

    # INA
    inaV = show_val("INA Vbus", buf, pos, 2, scale=100.0, unit=" V"); pos += 2
    inaI = show_val("INA Current", buf, pos, 2, scale=10.0, unit=" mA"); pos += 2
    inaP = show_val("INA Power", buf, pos, 2, scale=10.0, unit=" mW"); pos += 2

    # Energía acumulada
    energy_mWh = show_val("Energy", buf, pos, 4, scale=100.0, unit=" mWh"); pos += 4

    # Flags
    overCurrent = show_val("OverCurrent flag", buf, pos, 1); pos += 1
    okFlags = show_val("Sensor OK flags", buf, pos, 1); pos += 2

    # Stop byte
    if buf[pos] != 0x77:
        raise ValueError("Stop byte inválido")
    print(f"Stop byte: {hex(buf[pos])}")

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
query = f'from(bucket:"{bucket_src}") |> range(start: -1d) |> filter(fn: (r) => r["_field"] == "frame_hex")'
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