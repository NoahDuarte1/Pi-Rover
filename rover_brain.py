import paho.mqtt.client as mqtt
import json
import logging
import time
from datetime import datetime

# Logging setup — writes to file AND prints to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(f"rover_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
        logging.StreamHandler()
    ]
)

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

TOPIC_SENSORS = "rover/sensors"
TOPIC_STATUS = "rover/status"
TOPIC_CMD = "rover/cmd"

SAFE_DISTANCE = 20  # cm
TURN_DURATION = 1.0  # seconds to commit to a turn before reacting again

last_action_time = 0
avoiding = False


def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to MQTT broker (rc={rc})")
    client.subscribe(TOPIC_SENSORS)
    client.subscribe(TOPIC_STATUS)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = payload

    logging.info(f"[{topic}] {data}")

    if topic == TOPIC_SENSORS:
        avoid_obstacles(client, data)

def avoid_obstacles(client, data):
    global last_action_time, avoiding

    now = time.time()

    if avoiding and (now - last_action_time) < TURN_DURATION:
        logging.info(f"COOLDOWN active, ignoring. Time left: {TURN_DURATION - (now - last_action_time):.2f}s")
        return

    front = data['front']
    left = data['left']
    right = data['right']

    logging.info(f"DECISION CHECK - front:{front:.1f} left:{left:.1f} right:{right:.1f} avoiding:{avoiding}")

    if front < SAFE_DISTANCE:
        client.publish(TOPIC_CMD, "STOP")
        logging.info("Front obstacle! Stopping.")

        if left > right:
            client.publish(TOPIC_CMD, "LEFT:255")
            logging.info("Turning LEFT (more space)")
        else:
            client.publish(TOPIC_CMD, "RIGHT:255")
            logging.info("Turning RIGHT (more space)")

        avoiding = True
        last_action_time = now

    elif left < SAFE_DISTANCE:
        client.publish(TOPIC_CMD, "RIGHT:255")
        logging.info("Left obstacle! Turning RIGHT (away from it)")
        avoiding = True
        last_action_time = now

    elif right < SAFE_DISTANCE:
        client.publish(TOPIC_CMD, "LEFT:255")
        logging.info("Right obstacle! Turning LEFT (away from it)")
        avoiding = True
        last_action_time = now

    else:
        client.publish(TOPIC_CMD, "FORWARD:150")
        avoiding = False


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

logging.info("Rover brain started. Listening for sensors, GPS, status...")
client.loop_forever()
