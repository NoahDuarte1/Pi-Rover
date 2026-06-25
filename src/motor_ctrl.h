#ifndef MOTOR_CTRL_H
#define MOTOR_CTRL_H

#include <Arduino.h>

// Left side
#define ENA 14
#define IN1 27
#define IN2 26

// Right side
#define ENB 13
#define IN3 25
#define IN4 33

#define PWM_FREQ 1000
#define PWM_RES 8
#define ENA_CHANNEL 2
#define ENB_CHANNEL 3

#define DEFAULT_SPEED 200
void motorStop();

void motorSetup() {
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);

  ledcSetup(ENA_CHANNEL, PWM_FREQ, PWM_RES);
  ledcAttachPin(ENA, ENA_CHANNEL);

  ledcSetup(ENB_CHANNEL, PWM_FREQ, PWM_RES);
  ledcAttachPin(ENB, ENB_CHANNEL);

  motorStop();
}

void motorStop() {
  ledcWrite(ENA_CHANNEL, 0);
  ledcWrite(ENB_CHANNEL, 0);
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}

void motorForward(int speed = DEFAULT_SPEED) {
  ledcWrite(ENA_CHANNEL, speed);
  ledcWrite(ENB_CHANNEL, speed);
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void motorBackward(int speed = DEFAULT_SPEED) {
  ledcWrite(ENA_CHANNEL, speed);
  ledcWrite(ENB_CHANNEL, speed);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
}

void motorLeft(int speed = DEFAULT_SPEED) {
  ledcWrite(ENA_CHANNEL, speed);
  ledcWrite(ENB_CHANNEL, speed);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void motorRight(int speed = DEFAULT_SPEED) {
  ledcWrite(ENA_CHANNEL, speed);
  ledcWrite(ENB_CHANNEL, speed);
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
}

#endif