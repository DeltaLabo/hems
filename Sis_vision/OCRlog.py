import cv2
import pytesseract
import time
import csv
from datetime import datetime
from picamera2 import Picamera2
import os

# ---------- CONFIG ----------
INTERVALO = 5    # segundos entre mediciones
OUTPUT_FILE = "sper_data.csv"
MAX_SAMPLES = 100        # cantidad de mediciones

# ROI: ajustar el recorte de la pantalla para sólo leer el dato importante (y1:y2, x1:x2)
ROI_Y1, ROI_Y2 = 100, 200
ROI_X1, ROI_X2 = 150, 400

# Pytesseract config
TESSERACT_PSM = "--psm 7"  # una línea
# ----------------------------

def csv_row_count(path):
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        # restar header si existe
        lines = f.readlines()
        return max(0, len(lines) - 1)

def init_csv(path):
    exists = os.path.exists(path)
    if not exists:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "sper_uvab", "ocr_raw"])
    return

def ocr_from_roi(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # umbral adaptativo puede ayudar en pantallas con brillo variable
    _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)

    # recortar a ROI
    roi = thresh[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2]

    # intenta sólo dígitos (mejora reconocimiento)
    config = f"{TESSERACT_PSM} -c tessedit_char_whitelist=0123456789.,"
    text = pytesseract.image_to_string(roi, config=config)

    # normalizar decimal y limpiar
    text = text.replace(",", ".").strip()
    return text

def try_parse_float(s):
    try:
        return float(s)
    except:
        # intentar extraer número desde el string
        import re
        m = re.search(r"[-+]?\d*\.?\d+", s)
        if m:
            try:
                return float(m.group(0))
            except:
                return None
        return None

def main():
    init_csv(OUTPUT_FILE)
    picam2 = Picamera2()
    picam2.start()
    time.sleep(2)  # warm-up

    print(f"Iniciando logging. Se detendrá al alcanzar {MAX_SAMPLES} lecturas válidas en '{OUTPUT_FILE}'")
    try:
        while True:
            # comprobar cuántas filas ya hay
            count = csv_row_count(OUTPUT_FILE)
            if count >= MAX_SAMPLES:
                print(f"Se realizaron: {count} lecturas. Finalizando.")
                break

            frame = picam2.capture_array()
            ocr_raw = ocr_from_roi(frame)
            sper_val = try_parse_float(ocr_raw)

            timestamp = datetime.now().isoformat()

            with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, sper_val, ocr_raw])
                f.flush()

            print(f"[{timestamp}] Sper={sper_val}  (raw: '{ocr_raw}')  [{count+1}/{MAX_SAMPLES}]")

            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\nInterrumpido por usuario.")
    finally:
        picam2.stop()
        print("Archivo guardado:", OUTPUT_FILE)

if __name__ == "__main__":
    main()