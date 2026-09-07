#include <Arduino.h>

// XIAO ESP32S3
// A2 corresponde a GPIO3
const int PIN_ANEMOMETRO = A2;

// Calibración original voltaje -> velocidad
const float VOLTAJE_1 = 0.005;   // V
const float VELOCIDAD_1 = 0.0;   // m/s

const float VOLTAJE_2 = 0.45;    // V
const float VELOCIDAD_2 = 10.0;  // m/s

// Número de muestras para promediar el voltaje
const int NUM_MUESTRAS = 30;

// Corrección obtenida con tus datos de calibración:
//
// Velocidad patrón = 0.8466 * Velocidad medida + 2.7535
const float A_CALIBRACION = 0.8466;
const float B_CALIBRACION = 2.7535;


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


float calcularVelocidadOriginal(float voltaje) {

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


float calibrarVelocidad(float velocidadOriginal) {

  float velocidadCalibrada =
      A_CALIBRACION * velocidadOriginal +
      B_CALIBRACION;

  // Si prácticamente no hay señal,
  // considerar velocidad cero.
  if (velocidadOriginal <= 0.1) {
    velocidadCalibrada = 0.0;
  }

  return velocidadCalibrada;
}


void setup() {

  Serial.begin(115200);

  delay(1000);

  // ADC de 12 bits
  analogReadResolution(12);

  // Permite medir un rango mayor de voltaje
  analogSetPinAttenuation(PIN_ANEMOMETRO, ADC_11db);

  Serial.println();
  Serial.println("ANEMOMETRO");
  Serial.println("-----------------------------------------");
  Serial.println("Voltaje | Original | Calibrada");
}


void loop() {

  // Leer voltaje
  float voltaje = medirVoltaje();

  // Calcular velocidad usando la ecuación original
  float velocidadOriginal =
      calcularVelocidadOriginal(voltaje);

  // Aplicar la corrección experimental
  float velocidadCalibrada =
      calibrarVelocidad(velocidadOriginal);


  // Mostrar resultados
  Serial.print("Voltaje: ");
  Serial.print(voltaje, 3);
  Serial.print(" V");

  Serial.print(" | Original: ");
  Serial.print(velocidadOriginal, 2);
  Serial.print(" m/s");

  Serial.print(" | Calibrada: ");
  Serial.print(velocidadCalibrada, 2);
  Serial.println(" m/s");


  delay(500);
}