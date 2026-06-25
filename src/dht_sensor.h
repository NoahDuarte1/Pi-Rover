#ifndef DHT_SENSOR_H
#define DHT_SENSOR_H

#include <Arduino.h>
#include <DHT.h>

#define DHT_PIN 32

DHT dht(32, DHT11);

void dhtSetup(){
    dht.begin();
}

float readTemperature(){
    return dht.readTemperature();
}

float readHumidity(){
    return dht.readHumidity();
}

#endif