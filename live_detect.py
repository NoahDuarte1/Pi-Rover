from picamera2 import Picamera2
from libcamera import Transform
from ultralytics import YOLO
import time

picam2 = Picamera2()
config = picam2.create_still_configuration(transform=Transform(hflip=1, vflip=1))
picam2.configure(config)

picam2.set_controls({
    "AeEnable": False,
    "ExposureTime": 30000,
    "AnalogueGain": 2.5
})

picam2.start()
time.sleep(2)

model = YOLO("yolov8n.pt")

print("Starting live detection. Ctrl+C to stop.")

try:
    while True:
        frame = picam2.capture_array()
        results = model(frame, verbose=False)

        detections = results[0].boxes
        if len(detections) > 0:
            for box in detections:
                cls_name = model.names[int(box.cls)]
                conf = float(box.conf)
                print(f"Detected: {cls_name} ({conf:.2f})")
        else:
            print("No detections")

except KeyboardInterrupt:
    print("\nStopping")

picam2.stop()
