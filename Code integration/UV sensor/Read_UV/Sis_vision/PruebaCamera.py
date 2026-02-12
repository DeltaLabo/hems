import cv2

PIPE = ("libcamerasrc ! "
        "video/x-raw,format=RGB,width=640,height=480,framerate=30/1 ! "
        "videoconvert ! "
        "video/x-raw,format=BGR ! "
        "appsink drop=1 max-buffers=1 sync=false")

cap = cv2.VideoCapture(PIPE, cv2.CAP_GSTREAMER)
print("Opened:", cap.isOpened())
if not cap.isOpened():
    raise SystemExit("Could not open camera via GStreamer")

ok, frame = cap.read()
print("Read frame:", ok, "shape:", None if not ok else frame.shape)
cap.release()
