#include <Arduino.h>
#include "ultrasonic.h"
#include "servo_ctrl.h"
#include "indicators.h"
#include "dht_sensor.h"
#include "motor_ctrl.h"
#include "mqtt_client.h"

unsigned long lastSensorPublish = 0;
#define SENSOR_INTERVAL 500

void setup() {
  Serial.begin(115200);
  ultrasonicSetup();
  servoSetup();
  indicatorsSetup();
  dhtSetup();
  motorSetup();
  motorStop();
  mqttSetup();
  setLED(LED_GREEN, HIGH);
}

void loop() {
  mqttLoop();

  if (isKillSwitchPressed()) {
    motorStop();
    setLED(LED_BLUE, HIGH);
    mqtt.publish(TOPIC_STATUS, "killswitch");

    // Block until button released
    while (isKillSwitchPressed()) {
      mqttLoop();
      delay(50);
    }

    setLED(LED_BLUE, LOW);
    mqtt.publish(TOPIC_STATUS, "online");
    return;
  }

  setLED(LED_BLUE, LOW);

  unsigned long now = millis();
  if (now - lastSensorPublish >= SENSOR_INTERVAL) {
    lastSensorPublish = now;

    float front = readDistance(TRIG_FRONT, ECHO_FRONT);
    float left  = readDistance(TRIG_LEFT,  ECHO_LEFT);
    float right = readDistance(TRIG_RIGHT, ECHO_RIGHT);
    float temp  = readTemperature();
    float hum   = readHumidity();

    publishSensors(front, left, right, temp, hum);
  }
}