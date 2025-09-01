# -----------------------------------------------------------
# Just BW for 7-segment displays OCR
# -----------------------------------------------------------
import os
import re
import time
import cv2
import pytesseract

# -----------------------------------------------------------

CAM_INDEX = 0  # 0 = default webcam (/dev/video0 in Linux)

# ROI (Region of Interest) where the digits are located
x, y = 200, 200
w, h = 200, 100

# Tesseract config optimized for 7-segment digits
TESS_CFG = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'

# -----------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------
def preprocess_for_7seg(roi_bgr):
    """Preprocess ROI for OCR on 7-segment displays."""
    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return bw

def ocr_digits(img):
    """Run OCR restricted to digits only."""
    txt = pytesseract.image_to_string(img, config=TESS_CFG)
    digits = re.sub(r'[^0-9]', '', txt)  # keep only digits
    return digits

# -----------------------------------------------------------
# CAPTURE
# -----------------------------------------------------------
cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_ANY)
if not cap.isOpened():
    raise RuntimeError("Could not open camera")

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to grab frame")
            break

        # Extract ROI
        roi = frame[y:y+h, x:x+w]
        if roi.size == 0:
            continue

        # Enlarge ROI to help OCR
        roi = cv2.resize(roi, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

        # Preprocess for 7-segment
        bw = preprocess_for_7seg(roi)

        # OCR
        text = ocr_digits(bw)

        # Display text directly on the ROI
        if text:
            cv2.putText(bw, f"Reading: {text}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,), 2)

        # Show only the processed ROI in BW
        cv2.imshow("ROI - 7 Segment BW", bw)

        # Exit with ESC
        if cv2.waitKey(1) & 0xFF == ord('\x1b'):
            break

        time.sleep(0.01)

finally:
    cap.release()
    cv2.destroyAllWindows()