#ifndef SERVO_CTRL_H
#define SERVO_CTRL_H

#include <Arduino.h>
#include <ESP32Servo.h>

#define SERVO_PIN 23

Servo cameraServo;

void servoSetup() {
  cameraServo.attach(SERVO_PIN);
  cameraServo.write(90); // start at center
}

void servoTest() {
  // Sweep 0 to 180
  for (int angle = 0; angle <= 180; angle++) {
    cameraServo.write(angle);
    delay(15);
  }

  // Sweep 180 to 0
  for (int angle = 180; angle >= 0; angle--) {
    cameraServo.write(angle);
    delay(15);
  }
}

#endif