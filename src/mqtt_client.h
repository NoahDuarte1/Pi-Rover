#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "motor_ctrl.h"
#include "servo_ctrl.h"

#define WIFI_SSID "PiRover"
#define WIFI_PASS "rovernet123"
#define MQTT_BROKER "10.42.0.1"
#define MQTT_PORT 1883

// Topics
#define TOPIC_SENSORS   "rover/sensors"
#define TOPIC_CMD       "rover/cmd"
#define TOPIC_STATUS    "rover/status"
#define TOPIC_SERVO     "rover/servo"

WiFiClient espClient;
PubSubClient mqtt(espClient);

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  if (String(topic) == TOPIC_CMD) {
    Serial.print("CMD: "); Serial.println(msg);

    String cmd = msg;
    int speed = DEFAULT_SPEED;

    int colon = msg.indexOf(':');
    if (colon != -1) {
      cmd = msg.substring(0, colon);
      speed = msg.substring(colon + 1).toInt();
      speed = constrain(speed, 0, 255);
    }

    if      (cmd == "FORWARD")  motorForward(speed);
    else if (cmd == "BACKWARD") motorBackward(speed);
    else if (cmd == "LEFT")     motorLeft(speed);
    else if (cmd == "RIGHT")    motorRight(speed);
    else if (cmd == "STOP")     motorStop();
  }

  else if (String(topic) == TOPIC_SERVO) {
    int angle = msg.toInt();
    angle = constrain(angle, 0, 180);
    cameraServo.write(angle);
    Serial.print("Servo: "); Serial.println(angle);
  }
}

void mqttSetup() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to PiRover WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected, IP: " + WiFi.localIP().toString());

  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
}

void mqttReconnect() {
  while (!mqtt.connected()) {
    Serial.print("Connecting to MQTT...");
    if (mqtt.connect("ESP32Rover")) {
      Serial.println("connected");
      mqtt.subscribe(TOPIC_CMD);
      mqtt.subscribe(TOPIC_SERVO);
      mqtt.publish(TOPIC_STATUS, "online");
    } else {
      Serial.print("failed, rc=");
      Serial.println(mqtt.state());
      delay(2000);
    }
  }
}

void publishSensors(float front, float left, float right, float temp, float hum) {
  StaticJsonDocument<200> doc;
  doc["front"] = front;
  doc["left"] = left;
  doc["right"] = right;
  doc["temp"] = temp;
  doc["hum"] = hum;

  char buf[200];
  serializeJson(doc, buf);
  mqtt.publish(TOPIC_SENSORS, buf);
}

void mqttLoop() {
  if (!mqtt.connected()) mqttReconnect();
  mqtt.loop();
}

#endif