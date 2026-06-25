#ifndef ULTRASONIC_H
#define ULTRASONIC_H

#include <Arduino.h>

#define TRIG_FRONT 4
#define ECHO_FRONT 5
#define TRIG_LEFT 18
#define ECHO_LEFT 19
#define TRIG_RIGHT 21
#define ECHO_RIGHT 22

#define MAX_DISTANCE 400 // cm

void ultrasonicSetup() {
  pinMode(TRIG_FRONT, OUTPUT);
  pinMode(ECHO_FRONT, INPUT);
  pinMode(TRIG_LEFT, OUTPUT);
  pinMode(ECHO_LEFT, INPUT);
  pinMode(TRIG_RIGHT, OUTPUT);
  pinMode(ECHO_RIGHT, INPUT);
}


float readDistance(int trigPin, int echoPin) {
  // Send 10us trigger pulse
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Measure echo duration
  long duration = pulseIn(echoPin, HIGH, 30000); // 30ms timeout

  // If no echo received return max distance
  if (duration == 0) return MAX_DISTANCE;

  // Calculate distance in cm
  float distance = duration / 58.0;
  return distance;
}

#endif