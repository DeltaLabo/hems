#include <Wire.h>
#include "Adafruit_SHT31.h"
#include <SPI.h>
#include <SdFat.h>

// ---------- Configuración de pines SPI ----------
#define SD_CS   1   // Chip Select
#define SD_MOSI 9
#define SD_MISO 8
#define SD_SCK  7

// ---------- Objetos ----------
SdFat sd;
SdFile file;
Adafruit_SHT31 sht31 = Adafruit_SHT31();
void setup() {
  Serial.begin(115200);
  delay(500);

  // Inicializar sensor
  if (!sht31.begin(0x44)) {
    Serial.println(" No se encontró el sensor SHT31");
    while (1) delay(1000);
  }
  Serial.println(" Sensor SHT31 listo.");

  // Inicializar SD
  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
  Serial.println("Iniciando tarjeta SD...");
  if (!sd.begin(SD_CS, SD_SCK_MHZ(4))) {   // 4 MHz estable
    Serial.println(" Error al iniciar SD");
    sd.printSdError(&Serial);
    while (1) delay(1000);
  }
  Serial.println(" SD montada correctamente.");

  // Crear o abrir archivo CSV
  if (!file.open("datos.csv", O_WRITE | O_CREAT | O_APPEND)) {
    Serial.println(" Error al abrir/crear datos.csv");
    sd.printSdError(&Serial);
    while (1) delay(1000);
  }

  // Escribir encabezado si el archivo está vacío
  if (file.fileSize() == 0) {
    file.println("Temperatura(°C),Humedad(%)");
  }
  file.close();
  Serial.println("📄 Archivo datos.csv listo.");
}

void loop() {
  float temp = sht31.readTemperature();
  float hum  = sht31.readHumidity();
    //Lectura del sensor 
  if (!isnan(temp) && !isnan(hum)) {
    Serial.print("🌡️ ");
    Serial.print(temp, 2);
    Serial.print(" °C, 💧 ");
    Serial.print(hum, 2);
    Serial.println(" %");

    // Abrir archivo y guardar
    if (file.open("datos.csv", O_WRITE | O_APPEND)) {
      file.print(temp, 2);
      file.print(",");
      file.println(hum, 2);
      file.close();
      Serial.println(" Guardado en datos.csv\n");
    } else {
      Serial.println(" Error escribiendo en datos.csv");
      sd.printSdError(&Serial);
    }
  } else {
    Serial.println(" Error leyendo el sensor SHT31");
  }

  delay(1000); // cada 1 s
}

