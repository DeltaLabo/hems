from picamera2 import Picamera2
import cv2, time

picam2 = Picamera2()
cfg = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(cfg)
picam2.start()

time.sleep(0.5)  # pequeño warm-up
frame = picam2.capture_array()      # RGB
frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # a BGR para OpenCV
# ... aquí sigues con tu ROI + preprocesado + Tesseract
picam2.stop()