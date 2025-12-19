\
/*
  XIAO ESP32S3 — Multi‑sensor Logger to microSD (CSV)
  Sensors:
    - 2x SHT31 (I2C: 0x44 and 0x45)
    - AS7331 (SparkFun mini version) — I2C
    - BME280 (or BMP280 fallback) — I2C
  Storage:
    - microSD over SPI using SdFat
  Pins (taken from your Integration.ino):
    SD_CS=1, SD_MOSI=9, SD_MISO=8, SD_SCK=7

  CSV columns:
  timestamp_ms, sht1_T_C, sht1_RH_pct, sht2_T_C, sht2_RH_pct,
  uvA, uvB, uvC, env_T_C, env_P_hPa, env_RH_pct, sensor_ok_flags

  Libraries you’ll need (Library Manager):
  - Adafruit SHT31 Library
  - SparkFun AS7331 (SparkFun_AS7331)
  - Adafruit BME280 Library
  - Adafruit BMP280 Library
  - SdFat (by Bill Greiman)
*/

#include <Arduino.h>
#include <Wire.h>

// ----- SHT31 -----
#include "Adafruit_SHT31.h"

// ----- AS7331 (SparkFun) -----
#include <SparkFun_AS7331.h>

// ----- BME/BMP280 -----
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_BMP280.h>

// ----- microSD (SdFat) -----
#include <SPI.h>
#include <SdFat.h>

// ---------- SPI pins for SD ----------
#define SD_CS   1   // Chip Select
#define SD_MOSI 9
#define SD_MISO 8
#define SD_SCK  7

// ---------- I2C addresses ----------
#define SHT31_ADDR_1 0x44 //temp seca
#define SHT31_ADDR_2 0x45 //Globo
// BME280 typical: 0x76 or 0x77; BMP280 the same range
#define AS7331_I2C_ADDRESS 0x74 
// ---------- Objects ----------
Adafruit_SHT31 sht1 = Adafruit_SHT31();
Adafruit_SHT31 sht2 = Adafruit_SHT31();

SfeAS7331ArdI2C uv; // UV sensor

Adafruit_BME280 bme;   // prefer BME280 (has humidity)
Adafruit_BMP280 bmp;   // fallback if BME not found

bool haveSHT1 = false, haveSHT2 = false, haveUV = false;
bool haveBME = false, haveBMP = false;

SdFat sd;
SdFile file;

// ---------- Helpers ----------
bool initSD() {
  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
  // Use SdFat configuration for shared SPI; 25 MHz is safe for many modules; lower if needed
  if (!sd.begin(SdSpiConfig(SD_CS, SHARED_SPI, SD_SCK_MHZ(25)))) {
    Serial.println(F("SD init failed."));
    sd.printSdError(&Serial);
    return false;
  }

  if (!sd.exists("datos.csv")) {
    if (file.open("datos.csv", O_CREAT | O_WRITE)) {
      file.println(F("timestamp_ms,sht1_T_C,sht1_RH_pct,sht2_T_C,sht2_RH_pct,uvA,uvB,uvC,env_T_C,env_P_hPa,env_RH_pct,sensor_ok_flags"));
      file.close();
      Serial.println(F("Created datos.csv with header."));
    } else {
      Serial.println(F("Failed to create datos.csv"));
      return false;
    }
  }
  return true;
}

void appendCSV(uint32_t t_ms,
               float sht1T, float sht1RH,
               float sht2T, float sht2RH,
               float uvA, float uvB, float uvC,
               float envT, float envP_hPa, float envRH,
               uint16_t okFlags) {
  if (file.open("datos.csv", O_WRITE | O_APPEND)) {
    file.print(t_ms);
    file.print(',');
    file.print(isnan(sht1T) ? NAN : sht1T, 2);
    file.print(',');
    file.print(isnan(sht1RH) ? NAN : sht1RH, 2);
    file.print(',');
    file.print(isnan(sht2T) ? NAN : sht2T, 2);
    file.print(',');
    file.print(isnan(sht2RH) ? NAN : sht2RH, 2);
    file.print(',');
    file.print(isnan(uvA) ? NAN : uvA, 3);
    file.print(',');
    file.print(isnan(uvB) ? NAN : uvB, 3);
    file.print(',');
    file.print(isnan(uvC) ? NAN : uvC, 3);
    file.print(',');
    file.print(isnan(envT) ? NAN : envT, 2);
    file.print(',');
    file.print(isnan(envP_hPa) ? NAN : envP_hPa, 2);
    file.print(',');
    file.print(isnan(envRH) ? NAN : envRH, 2);
    file.print(',');
    file.println(okFlags); // bitmask of which sensors were OK
    file.close();
  } else {
    Serial.println(F("Error opening datos.csv for append."));
    sd.printSdError(&Serial);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }

  Serial.println(F("\nXIAO ESP32S3 Multi‑sensor Logger"));

  Wire.begin(); // Default pins for XIAO ESP32S3

  // ---- SHT31 #1 ----
  haveSHT1 = sht1.begin(SHT31_ADDR_1);
  if (haveSHT1) {
    sht1.heater(false);
    Serial.println(F("SHT31 #1 OK (0x44)."));
  } else {
    Serial.println(F("SHT31 #1 NOT found (0x44)."));
  }

  // ---- SHT31 #2 ----
  haveSHT2 = sht2.begin(SHT31_ADDR_2);
  if (haveSHT2) {
    sht2.heater(false);
    Serial.println(F("SHT31 #2 OK (0x45)."));
  } else {
    Serial.println(F("SHT31 #2 NOT found (0x45)."));
  }

  // ---- AS7331 UV ----
if (uv.begin(AS7331_I2C_ADDRESS, Wire) == ksfTkErrOk) {
  haveUV = true;
  Serial.println(F("AS7331 UV OK."));
} else {
  haveUV = false;
  Serial.println(F("AS7331 UV NOT found."));
}

  // ---- Env sensor: try BME280 then BMP280 ----
  // Try both 0x76 and 0x77 for convenience
  if (bme.begin(0x76) || bme.begin(0x77)) {
    haveBME = true;
    Serial.println(F("BME280 OK."));
  } else if (bmp.begin(0x76) || bmp.begin(0x77)) {
    haveBMP = true;
    Serial.println(F("BMP280 OK (no humidity)."));
  } else {
    Serial.println(F("BME/BMP280 NOT found."));
  }

  // ---- microSD ----
  initSD();
}

uint32_t lastPrint = 0;
const uint32_t LOG_PERIOD_MS = 1000; // 1 s

void loop() {
  uint32_t now = millis();
  if (now - lastPrint < LOG_PERIOD_MS) return;
  lastPrint = now;

  // --- Read SHT31 #1 ---
  float sht1T = NAN, sht1RH = NAN;
  bool sht1OK = false;
  if (haveSHT1) {
    sht1T = sht1.readTemperature();
    sht1RH = sht1.readHumidity();
    sht1OK = (!isnan(sht1T) && !isnan(sht1RH));
    if (!sht1OK) Serial.println(F("Warn: SHT31 #1 read error."));
  }

  // --- Read SHT31 #2 ---
  float sht2T = NAN, sht2RH = NAN;
  bool sht2OK = false;
  if (haveSHT2) {
    sht2T = sht2.readTemperature();
    sht2RH = sht2.readHumidity();
    sht2OK = (!isnan(sht2T) && !isnan(sht2RH));
    if (!sht2OK) Serial.println(F("Warn: SHT31 #2 read error."));
  }

  // --- Read AS7331 UV ---
  float uvA = NAN, uvB = NAN, uvC = NAN;
  bool uvOK = false;
  if (haveUV) {
    // Allow conversion time (example: minimal wait, library may handle it internally too)
    delay(2 + uv.getConversionTimeMillis());
    if (uv.readAllUV() == ksfTkErrOk) {
      uvA = uv.getUVA();
      uvB = uv.getUVB();
      uvC = uv.getUVC();
      uvOK = true;
    } else {
      Serial.println(F("Warn: AS7331 read error."));
    }
  }

  // --- Read Env (BME or BMP) ---
  float envT = NAN, envP_hPa = NAN, envRH = NAN;
  bool envOK = false;
  if (haveBME) {
    envT = bme.readTemperature();
    envP_hPa = bme.readPressure() / 100.0f; // Pa -> hPa
    envRH = bme.readHumidity();
    envOK = (!isnan(envT) && !isnan(envP_hPa) && !isnan(envRH));
    if (!envOK) Serial.println(F("Warn: BME280 read issue."));
  } else if (haveBMP) {
    envT = bmp.readTemperature();
    envP_hPa = bmp.readPressure() / 100.0f;
    envRH = NAN; // Not available
    envOK = (!isnan(envT) && !isnan(envP_hPa));
    if (!envOK) Serial.println(F("Warn: BMP280 read issue."));
  }

  // --- Pack a simple bitmask for status flags (1 = OK) ---
  // bit0: SHT1, bit1: SHT2, bit2: UV, bit3: ENV
  uint16_t okFlags = 0;
  if (sht1OK) okFlags |= (1 << 0);
  if (sht2OK) okFlags |= (1 << 1);
  if (uvOK)   okFlags |= (1 << 2);
  if (envOK)  okFlags |= (1 << 3);

  // --- Serial print (CSV one-liner) ---
  Serial.print(now); Serial.print(',');
  Serial.print(isnan(sht1T)?NAN:sht1T,2); Serial.print(',');
  Serial.print(isnan(sht1RH)?NAN:sht1RH,2); Serial.print(',');
  Serial.print(isnan(sht2T)?NAN:sht2T,2); Serial.print(',');
  Serial.print(isnan(sht2RH)?NAN:sht2RH,2); Serial.print(',');
  Serial.print(isnan(uvA)?NAN:uvA,3); Serial.print(',');
  Serial.print(isnan(uvB)?NAN:uvB,3); Serial.print(',');
  Serial.print(isnan(uvC)?NAN:uvC,3); Serial.print(',');
  Serial.print(isnan(envT)?NAN:envT,2); Serial.print(',');
  Serial.print(isnan(envP_hPa)?NAN:envP_hPa,2); Serial.print(',');
  Serial.print(isnan(envRH)?NAN:envRH,2); Serial.print(',');
  Serial.println(okFlags);

  // --- Append to SD ---
  appendCSV(now, sht1T, sht1RH, sht2T, sht2RH,
            uvA, uvB, uvC,
            envT, envP_hPa, envRH,
            okFlags);
}

void appendCSV(uint32_t t_ms,
               float sht1T, float sht1RH,
               float sht2T, float sht2RH,
               float uvA, float uvB, float uvC,
               float envT, float envP_hPa, float envRH,
               uint16_t okFlags) {
  if (file.open("datos.csv", O_WRITE | O_APPEND)) {
    file.print(t_ms);
    file.print(',');
    file.print(isnan(sht1T) ? NAN : sht1T, 2);
    file.print(',');
    file.print(isnan(sht1RH) ? NAN : sht1RH, 2);
    file.print(',');
    file.print(isnan(sht2T) ? NAN : sht2T, 2);
    file.print(',');
    file.print(isnan(sht2RH) ? NAN : sht2RH, 2);
    file.print(',');
    file.print(isnan(uvA) ? NAN : uvA, 3);
    file.print(',');
    file.print(isnan(uvB) ? NAN : uvB, 3);
    file.print(',');
    file.print(isnan(uvC) ? NAN : uvC, 3);
    file.print(',');
    file.print(isnan(envT) ? NAN : envT, 2);
    file.print(',');
    file.print(isnan(envP_hPa) ? NAN : envP_hPa, 2);
    file.print(',');
    file.print(isnan(envRH) ? NAN : envRH, 2);
    file.print(',');
    file.println(okFlags); // bitmask of which sensors were OK
    file.close();
  } else {
    Serial.println(F("Error opening datos.csv for append."));
    sd.printSdError(&Serial);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }

  Serial.println(F("\nXIAO ESP32S3 Multi‑sensor Logger"));

  Wire.begin(); // Default pins for XIAO ESP32S3

  // ---- SHT31 #1 ----
  haveSHT1 = sht1.begin(SHT31_ADDR_1);
  if (haveSHT1) {
    sht1.heater(false);
    Serial.println(F("SHT31 #1 OK (0x44)."));
  } else {
    Serial.println(F("SHT31 #1 NOT found (0x44)."));
  }

  // ---- SHT31 #2 ----
  haveSHT2 = sht2.begin(SHT31_ADDR_2);
  if (haveSHT2) {
    sht2.heater(false);
    Serial.println(F("SHT31 #2 OK (0x45)."));
  } else {
    Serial.println(F("SHT31 #2 NOT found (0x45)."));
  }

  // ---- AS7331 UV ----
  if (uv.begin(Wire) == ksfTkErrOk) {
    haveUV = true;
    // Example: leave default integration settings; you can adjust if needed.
    Serial.println(F("AS7331 UV OK."));
  } else {
    haveUV = false;
    Serial.println(F("AS7331 UV NOT found."));
  }

  // ---- Env sensor: try BME280 then BMP280 ----
  // Try both 0x76 and 0x77 for convenience
  if (bme.begin(0x76) || bme.begin(0x77)) {
    haveBME = true;
    Serial.println(F("BME280 OK."));
  } else if (bmp.begin(0x76) || bmp.begin(0x77)) {
    haveBMP = true;
    Serial.println(F("BMP280 OK (no humidity)."));
  } else {
    Serial.println(F("BME/BMP280 NOT found."));
  }

  // ---- microSD ----
  initSD();
}

uint32_t lastPrint = 0;
const uint32_t LOG_PERIOD_MS = 1000; // 1 s

void loop() {
  uint32_t now = millis();
  if (now - lastPrint < LOG_PERIOD_MS) return;
  lastPrint = now;

  // --- Read SHT31 #1 ---
  float sht1T = NAN, sht1RH = NAN;
  bool sht1OK = false;
  if (haveSHT1) {
    sht1T = sht1.readTemperature();
    sht1RH = sht1.readHumidity();
    sht1OK = (!isnan(sht1T) && !isnan(sht1RH));
    if (!sht1OK) Serial.println(F("Warn: SHT31 #1 read error."));
  }

  // --- Read SHT31 #2 ---
  float sht2T = NAN, sht2RH = NAN;
  bool sht2OK = false;
  if (haveSHT2) {
    sht2T = sht2.readTemperature();
    sht2RH = sht2.readHumidity();
    sht2OK = (!isnan(sht2T) && !isnan(sht2RH));
    if (!sht2OK) Serial.println(F("Warn: SHT31 #2 read error."));
  }

  // --- Read AS7331 UV ---
  float uvA = NAN, uvB = NAN, uvC = NAN;
  bool uvOK = false;
  if (haveUV) {
    // Allow conversion time (example: minimal wait, library may handle it internally too)
    delay(2 + uv.getConversionTimeMillis());
    if (uv.readAllUV() == ksfTkErrOk) {
      uvA = uv.getUVA();
      uvB = uv.getUVB();
      uvC = uv.getUVC();
      uvOK = true;
    } else {
      Serial.println(F("Warn: AS7331 read error."));
    }
  }

  // --- Read Env (BME or BMP) ---
  float envT = NAN, envP_hPa = NAN, envRH = NAN;
  bool envOK = false;
  if (haveBME) {
    envT = bme.readTemperature();
    envP_hPa = bme.readPressure() / 100.0f; // Pa -> hPa
    envRH = bme.readHumidity();
    envOK = (!isnan(envT) && !isnan(envP_hPa) && !isnan(envRH));
    if (!envOK) Serial.println(F("Warn: BME280 read issue."));
  } else if (haveBMP) {
    envT = bmp.readTemperature();
    envP_hPa = bmp.readPressure() / 100.0f;
    envRH = NAN; // Not available
    envOK = (!isnan(envT) && !isnan(envP_hPa));
    if (!envOK) Serial.println(F("Warn: BMP280 read issue."));
  }

  // --- Pack a simple bitmask for status flags (1 = OK) ---
  // bit0: SHT1, bit1: SHT2, bit2: UV, bit3: ENV
  uint16_t okFlags = 0;
  if (sht1OK) okFlags |= (1 << 0);
  if (sht2OK) okFlags |= (1 << 1);
  if (uvOK)   okFlags |= (1 << 2);
  if (envOK)  okFlags |= (1 << 3);

  // --- Serial print (CSV one-liner) ---
  Serial.print(now); Serial.print(',');
  Serial.print(isnan(sht1T)?NAN:sht1T,2); Serial.print(',');
  Serial.print(isnan(sht1RH)?NAN:sht1RH,2); Serial.print(',');
  Serial.print(isnan(sht2T)?NAN:sht2T,2); Serial.print(',');
  Serial.print(isnan(sht2RH)?NAN:sht2RH,2); Serial.print(',');
  Serial.print(isnan(uvA)?NAN:uvA,3); Serial.print(',');
  Serial.print(isnan(uvB)?NAN:uvB,3); Serial.print(',');
  Serial.print(isnan(uvC)?NAN:uvC,3); Serial.print(',');
  Serial.print(isnan(envT)?NAN:envT,2); Serial.print(',');
  Serial.print(isnan(envP_hPa)?NAN:envP_hPa,2); Serial.print(',');
  Serial.print(isnan(envRH)?NAN:envRH,2); Serial.print(',');
  Serial.println(okFlags);

  // --- Append to SD ---
  appendCSV(now, sht1T, sht1RH, sht2T, sht2RH,
            uvA, uvB, uvC,
            envT, envP_hPa, envRH,
            okFlags);
}
