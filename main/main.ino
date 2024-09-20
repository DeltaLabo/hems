#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <ESP32Time.h>  //Libreria para usar el timer
#include <WiFi.h>

#define DEBUG false

// Definición de la red WiFi
const char* ssid = "Grace";   // Tu red WiFi SSID
const char* password = "Sanfra24";    // Tu contraseña WiFi

// NTP server
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 0;  // GMT -6
const int daylightOffset_sec = 0;

ESP32Time rtc(-21600); 

hw_timer_t *timer = NULL;

#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_BME280 bme1; // I2C
Adafruit_BME280 bme2; // I2C

bool timer_flag = true;

void ARDUINO_ISR_ATTR onTimer() {
  timer_flag = true;
}

void setup() {
  Serial.begin(9600);
  // Inicializar sensores
  if ( bme1.begin(0x76) & bme2.begin(0x77)) {
    if (DEBUG) Serial.println("BME280 sensors in address 0x76 and 0x77 conected");
  }
  else{ 
    Serial.println("Could not find a valid BME280 sensor, check wiring!");
    while (1);
  }
  // Conectar a la red WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    if (DEBUG) Serial.print(".");
  }
  if (DEBUG) Serial.println("Connected to WiFi");
  // Sincronizar tiempo
  syncTime(DEBUG);
  // Set timer frequency to 1Mhz
  timer = timerBegin(1000000);
  // Attach onTimer function to our timer.
  timerAttachInterrupt(timer, &onTimer);
  // Set alarm to call onTimer function every second (value in microseconds).
  // Repeat the alarm (third parameter) with unlimited count = 0 (fourth parameter).
  timerAlarm(timer, 1000000, true, 0);
}

void loop() {
  // Ejecuta la función de impresión si la bandera está activa
  if (timer_flag) {
    printValues();    
    timer_flag = false; // Resetea la bandera
  }
}

void printValues() {
  // Imprime los datos del Sensor 1
  String now = rtc.getTime("%Y-%m-%d %H:%M:%S,");
  Serial.print(now);
  Serial.print("1,"); // Identificador del sensor
  Serial.print(bme1.readTemperature()); // Temperatura
  Serial.print(","); 
  Serial.print(bme1.readPressure() / 100.0F); // Presión en hPa
  Serial.print(",");
  Serial.print(bme1.readHumidity()); // Humedad
  Serial.println(); // Finaliza la línea
  // Imprime los datos del Sensor 2
  Serial.print(now);
  Serial.print("2,"); // Identificador del sensor
  Serial.print(bme2.readTemperature()); // Temperatura
  Serial.print(","); 
  Serial.print(bme2.readPressure() / 100.0F); // Presión en hPa
  Serial.print(",");
  Serial.print(bme2.readHumidity()); // Humedad
  Serial.println(); // Finaliza la línea
}

void syncTime(bool debug) {
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  if (debug) Serial.println("Waiting for NTP time sync");
  unsigned long startMillis = millis();
  while (millis() - startMillis < 10000) {  // Espera hasta 10 segundos para sincronizar
    if (time(nullptr) > 0) {  // Verifica si se ha sincronizado el tiempo
      rtc.setTime(time(nullptr)); // Ajusta la hora actual
      if(debug) Serial.println("Time synced!");
      return;
    }
    delay(500);
    if (debug) Serial.print(".");
  }
  if (debug) Serial.println("Failed to sync time.");
}