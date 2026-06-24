from picamera2 import Picamera2
from libcamera import Transform
from ultralytics import YOLO
import paho.mqtt.client as mqtt
import time
import sys

if len(sys.argv) < 2:
    print("Usage: python3 follow_object.py <object_name>")
    sys.exit(1)

TARGET_CLASS = sys.argv[1].lower()

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_CMD = "rover/cmd"

FRAME_WIDTH = 640
CENTER_TOLERANCE = 60
TARGET_BOX_HEIGHT = 400
MIN_CONFIDENCE = 0.5

ROTATION_TIME = 6.0          # seconds for one full 360 spin at speed 255
MAX_SEARCH_TIME = ROTATION_TIME * 2  # 2 full spins = 12 seconds

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

picam2 = Picamera2()
config = picam2.create_still_configuration(
    main={"size": (FRAME_WIDTH, 480)},
    transform=Transform(hflip=1, vflip=1)
)
picam2.configure(config)

picam2.set_controls({
    "AeEnable": False,
    "ExposureTime": 30000,
    "AnalogueGain": 2.5
})

picam2.start()
time.sleep(2)

model = YOLO("yolov8n.pt")

print(f"Searching for '{TARGET_CLASS}'. Ctrl+C to stop.")

search_start_time = None  # None means "not currently searching"
gave_up = False

try:
    while True:
        if gave_up:
            print("Gave up searching. Idle.")
            time.sleep(1)
            continue

        frame = picam2.capture_array()
        results = model(frame, verbose=False)

        best_match = None
        best_conf = 0

        for box in results[0].boxes:
            cls_name = model.names[int(box.cls)]
            conf = float(box.conf)

            if cls_name == TARGET_CLASS and conf > MIN_CONFIDENCE and conf > best_conf:
                best_match = box
                best_conf = conf

        if best_match is None:
            # Object not visible — search mode
            if search_start_time is None:
                search_start_time = time.time()
                print(f"'{TARGET_CLASS}' not visible. Starting search.")

            elapsed = time.time() - search_start_time

            if elapsed >= MAX_SEARCH_TIME:
                client.publish(TOPIC_CMD, "STOP")
                print(f"Searched {MAX_SEARCH_TIME}s, no '{TARGET_CLASS}' found. Giving up.")
                gave_up = True
            else:
                client.publish(TOPIC_CMD, "LEFT:255")
                print(f"Searching... {elapsed:.1f}s / {MAX_SEARCH_TIME}s")

        else:
            # Object found — reset search timer, track it
            search_start_time = None

            x1, y1, x2, y2 = best_match.xyxy[0]
            box_center_x = (x1 + x2) / 2
            box_height = y2 - y1

            frame_center_x = FRAME_WIDTH / 2
            offset = box_center_x - frame_center_x

            print(f"Found '{TARGET_CLASS}' conf:{best_conf:.2f} offset:{offset:.0f} height:{box_height:.0f}")

            if offset < -CENTER_TOLERANCE:
                client.publish(TOPIC_CMD, "LEFT:255")
                print("Turning LEFT to center")
            elif offset > CENTER_TOLERANCE:
                client.publish(TOPIC_CMD, "RIGHT:255")
                print("Turning RIGHT to center")
            else:
                if box_height < TARGET_BOX_HEIGHT:
                    client.publish(TOPIC_CMD, "FORWARD:200")
                    print("Driving FORWARD")
                else:
                    client.publish(TOPIC_CMD, "STOP")
                    print("Close enough. Stopping.")

except KeyboardInterrupt:
    print("\nStopping")
    client.publish(TOPIC_CMD, "STOP")

picam2.stop()
