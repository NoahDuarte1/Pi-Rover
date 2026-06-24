from flask import Flask, render_template, Response, request
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
from picamera2 import Picamera2
from libcamera import Transform
import cv2
import time
import threading
from ultralytics import YOLO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rover_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

TOPIC_SENSORS = "rover/sensors"
TOPIC_STATUS = "rover/status"
TOPIC_CMD = "rover/cmd"
TOPIC_SERVO = "rover/servo"

# --- Mode state ---
current_mode = "manual"
find_object_target = ""

# --- Shared camera frame ---
latest_frame = None
frame_lock = threading.Lock()

# --- YOLO ---
model = YOLO("yolov8n.pt")

# --- Follow/Find constants ---
FRAME_WIDTH = 640
CENTER_TOLERANCE = 60
TARGET_BOX_HEIGHT = 400
MIN_CONFIDENCE = 0.5
ROTATION_TIME = 6.0
MAX_SEARCH_TIME = ROTATION_TIME * 2


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    print("Browser client connected")


def on_mqtt_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = payload

    if topic == TOPIC_SENSORS:
        socketio.emit('sensor_update', data)
    elif topic == TOPIC_STATUS:
        socketio.emit('status_update', data)


mqtt_client = mqtt.Client()
mqtt_client.on_message = on_mqtt_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.subscribe(TOPIC_SENSORS)
mqtt_client.subscribe(TOPIC_STATUS)
mqtt_client.loop_start()


# --- Camera setup ---
picam2 = Picamera2()
camera_config = picam2.create_video_configuration(
    main={"size": (FRAME_WIDTH, 480)},
    transform=Transform(hflip=1, vflip=1)
)
picam2.configure(camera_config)
picam2.start()
time.sleep(2)


def capture_loop():
    global latest_frame
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        with frame_lock:
            latest_frame = frame


threading.Thread(target=capture_loop, daemon=True).start()


def generate_frames():
    while True:
        with frame_lock:
            frame = latest_frame
        if frame is None:
            time.sleep(0.05)
            continue
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


def detection_loop():
    global current_mode, find_object_target

    search_start_time = None
    gave_up = False

    while True:
        if current_mode == "manual":
            search_start_time = None
            gave_up = False
            time.sleep(0.1)
            continue

        with frame_lock:
            frame = latest_frame

        if frame is None:
            time.sleep(0.1)
            continue

        if current_mode == "follow_person":
            target_class = "person"
        elif current_mode == "find_object":
            target_class = find_object_target
        else:
            time.sleep(0.1)
            continue

        results = model(frame, verbose=False)

        best_match = None
        best_conf = 0

        for box in results[0].boxes:
            cls_name = model.names[int(box.cls)]
            conf = float(box.conf)
            if cls_name == target_class and conf > MIN_CONFIDENCE and conf > best_conf:
                best_match = box
                best_conf = conf

        if best_match is None:
            if gave_up:
                time.sleep(0.1)
                continue

            if search_start_time is None:
                search_start_time = time.time()

            elapsed = time.time() - search_start_time

            if elapsed >= MAX_SEARCH_TIME:
                mqtt_client.publish(TOPIC_CMD, "STOP")
                print(f"Gave up searching for '{target_class}'")
                gave_up = True
            else:
                mqtt_client.publish(TOPIC_CMD, "LEFT:255")
        else:
            search_start_time = None
            gave_up = False

            x1, y1, x2, y2 = best_match.xyxy[0]
            box_center_x = (x1 + x2) / 2
            box_height = y2 - y1
            offset = box_center_x - (FRAME_WIDTH / 2)

            if offset < -CENTER_TOLERANCE:
                mqtt_client.publish(TOPIC_CMD, "LEFT:255")
            elif offset > CENTER_TOLERANCE:
                mqtt_client.publish(TOPIC_CMD, "RIGHT:255")
            else:
                if box_height < TARGET_BOX_HEIGHT:
                    mqtt_client.publish(TOPIC_CMD, "FORWARD:200")
                else:
                    mqtt_client.publish(TOPIC_CMD, "STOP")


threading.Thread(target=detection_loop, daemon=True).start()


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/cmd', methods=['POST'])
def send_cmd():
    command = request.json.get('command')
    mqtt_client.publish(TOPIC_CMD, command)
    return {'status': 'ok'}


@app.route('/servo', methods=['POST'])
def send_servo():
    angle = request.json.get('angle')
    mqtt_client.publish(TOPIC_SERVO, str(angle))
    return {'status': 'ok'}


@app.route('/mode', methods=['POST'])
def set_mode():
    global current_mode, find_object_target
    data = request.json
    current_mode = data.get('mode', 'manual')
    find_object_target = data.get('target', '').lower()
    mqtt_client.publish(TOPIC_CMD, "STOP")
    print(f"Mode: {current_mode} target: {find_object_target}")
    return {'status': 'ok'}


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)