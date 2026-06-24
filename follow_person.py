from picamera2 import Picamera2
from libcamera import Transform
from ultralytics import YOLO
import paho.mqtt.client as mqtt
import time

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_CMD = "rover/cmd"

# Frame settings
FRAME_WIDTH = 640
CENTER_TOLERANCE = 60       # pixels — how far off-center is "close enough"
TARGET_BOX_HEIGHT = 400     # pixels — calibrate this based on testing
MIN_CONFIDENCE = 0.5

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

print("Person following started. Ctrl+C to stop.")

try:
    while True:
        frame = picam2.capture_array()
        results = model(frame, verbose=False)

        # Find the highest-confidence person detection
        best_person = None
        best_conf = 0

        for box in results[0].boxes:
            cls_name = model.names[int(box.cls)]
            conf = float(box.conf)

            if cls_name == "person" and conf > MIN_CONFIDENCE and conf > best_conf:
                best_person = box
                best_conf = conf

        if best_person is None:
            client.publish(TOPIC_CMD, "STOP")
            print("No person found. Stopping.")
        else:
            x1, y1, x2, y2 = best_person.xyxy[0]
            box_center_x = (x1 + x2) / 2
            box_height = y2 - y1

            frame_center_x = FRAME_WIDTH / 2
            offset = box_center_x - frame_center_x

            print(f"Person conf:{best_conf:.2f} center_offset:{offset:.0f} height:{box_height:.0f}")

            # Decide direction
            if offset < -CENTER_TOLERANCE:
                client.publish(TOPIC_CMD, "LEFT:255")
                print("Turning LEFT to center person")
            elif offset > CENTER_TOLERANCE:
                client.publish(TOPIC_CMD, "RIGHT:255")
                print("Turning RIGHT to center person")
            else:
                # Person is centered, check distance
                if box_height < TARGET_BOX_HEIGHT:
                    client.publish(TOPIC_CMD, "FORWARD:255")
                    print("Driving FORWARD toward person")
                else:
                    client.publish(TOPIC_CMD, "STOP")
                    print("Close enough. Stopping.")

except KeyboardInterrupt:
    print("\nStopping")
    client.publish(TOPIC_CMD, "STOP")

picam2.stop()
