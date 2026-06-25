#ifndef INDICATORS_H
#define INDICATORS_H

#include <Arduino.h>

#define BUTTON 36
#define LED_BLUE 15
#define LED_GREEN 2

void indicatorsSetup() {
    pinMode(LED_BLUE, OUTPUT);
    pinMode(LED_GREEN, OUTPUT);
    pinMode(BUTTON, INPUT);
}

void setLED(int pin, bool state){
    digitalWrite(pin, state);
}
bool isKillSwitchPressed(){
    return !digitalRead(BUTTON);
}

#endif