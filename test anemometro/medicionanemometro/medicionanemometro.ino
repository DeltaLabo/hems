#include <Arduino.h>

// XIAO ESP32S3: A2 corresponde a GPIO3
const int PIN_ANEMOMETRO = A2;

// Valores obtenidos durante la calibración
const float VOLTAJE_1 = 0.005;      // V
const float VELOCIDAD_1 = 0.0;     // m/s

const float VOLTAJE_2 = 0.6;      // V
const float VELOCIDAD_2 = 10.0;    // m/s

const int NUM_MUESTRAS = 30;

void setup() {
  Serial.begin(115200);
  delay(1000);

  analogReadResolution(12);
  analogSetPinAttenuation(PIN_ANEMOMETRO, ADC_11db);

  Serial.println("Anemometro listo");
  Serial.println("Voltaje (V), Velocidad (m/s)");
}

void loop() {
  float voltaje = medirVoltaje();
  float velocidad = calcularVelocidad(voltaje);

  Serial.print("Voltaje: ");
  Serial.print(voltaje, 3);
  Serial.print(" V | Velocidad: ");
  Serial.print(velocidad, 2);
  Serial.println(" m/s");

  delay(500);
}

float medirVoltaje() {
  uint32_t sumaMilivoltios = 0;

  for (int i = 0; i < NUM_MUESTRAS; i++) {
    sumaMilivoltios += analogReadMilliVolts(PIN_ANEMOMETRO);
    delay(5);
  }

  float promedioMilivoltios =
    sumaMilivoltios / (float)NUM_MUESTRAS;

  return promedioMilivoltios / 1000.0;
}

float calcularVelocidad(float voltaje) {
  if (VOLTAJE_2 == VOLTAJE_1) {
    return 0.0;
  }

  float pendiente =
    (VELOCIDAD_2 - VELOCIDAD_1) /
    (VOLTAJE_2 - VOLTAJE_1);

  float velocidad =
    VELOCIDAD_1 +
    pendiente * (voltaje - VOLTAJE_1);

  if (velocidad < 0.0) {
    velocidad = 0.0;
  }

  return velocidad;
}