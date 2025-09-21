import cv2
from picamera2 import Picamera2
import pytesseract
import time

# Inicializar cámara
picam2 = Picamera2()
picam2.start()
time.sleep(2)

# Variables globales para ROI
roi_start = None
roi_end = None
drawing = False
current_roi = None

def mouse_callback(event, x, y, flags, param):
    global roi_start, roi_end, drawing, current_roi

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        roi_start = (x, y)
        roi_end = None

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            roi_end = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi_end = (x, y)
        if roi_start and roi_end:
            x1, y1 = roi_start
            x2, y2 = roi_end
            current_roi = (min(y1, y2), max(y1, y2), min(x1, x2), max(x1, x2))
            print("ROI definido:", current_roi)

# Crear ventana y setear callback
cv2.namedWindow("ROI Selector")
cv2.setMouseCallback("ROI Selector", mouse_callback)

print("Dibuja un rectángulo sobre el número grande. Presiona 'q' para salir.")

while True:
    frame = picam2.capture_array()
    display = frame.copy()

    # Dibujar rectángulo mientras arrastras
    if roi_start and roi_end:
        cv2.rectangle(display, roi_start, roi_end, (0, 255, 0), 2)

    # Si ya hay ROI definido, mostrar OCR de esa región
    if current_roi:
        y1, y2, x1, x2 = current_roi
        roi = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)
        text = pytesseract.image_to_string(thresh, config="--psm 7 digits")
        cv2.putText(display, f"OCR: {text.strip()}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("ROI Selector", display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()

if current_roi:
    print("ROI final:", current_roi, " -> usar como (y1:y2, x1:x2)")
else:
    print("No se seleccionó ROI.")
