#include <Wire.h>
#include <AS7331.h>

#define AS7331_I2C_ADDRESS 0x74
#define AS7331_INT_PIN 2

AS7331 uv(AS7331_I2C_ADDRESS);
volatile bool readyFlag = false;

void uvReadyISR() {
  readyFlag = true; // bandera indica que la medición terminó
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  Wire.begin();

  pinMode(AS7331_INT_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(AS7331_INT_PIN), uvReadyISR, RISING);

  if (uv.begin()) {
    Serial.println("AS7331 detectado");
    uv.powerUp();
    uv.setConversionTime(AS7331_CONV_512); // ajustable: 64,128,256,512,1024 ms
  } else {
    Serial.println("AS7331 NO detectado");
  }

  // Primer medición
  uv.startMeasurement();
}

void loop() {
  if (readyFlag) { // solo cuando la medición está lista
    float uvA = uv.getUVA_uW();
    float uvB = uv.getUVB_uW();
    float uvC = uv.getUVC_uW();

    Serial.print("UVA: "); Serial.print(uvA);
    Serial.print(" UVB: "); Serial.print(uvB);
    Serial.print(" UVC: "); Serial.println(uvC);

    readyFlag = false;
    uv.startMeasurement(); // inicia la siguiente medición
  }
}