/*
  XIAO ESP32S3 — Multi-sensor Logger to microSD (CSV), with Wi-Fi + NTP datetime

  Sensors:
    - 2x SHT31 (I2C: 0x44 and 0x45)
    - AS7331 (SparkFun mini version) — I2C
    - BME280 (or BMP280 fallback) — I2C
    - INA219 (Elegoo, shunt 0.1 ohm) — I2C

  Storage:
    - microSD over SPI using SdFat

  CSV columns:
  datetime_iso8601, timestamp_ms,
  sht1_T_C, sht1_RH_pct,
  sht2_T_C, sht2_RH_pct,
  uvA, uvB, uvC,
  env_T_C, env_P_hPa, env_RH_pct,
  ina_Vbus, ina_current_mA, ina_power_mW,
  energy_mWh, overcurrent_flag,
  sensor_ok_flags
*/

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <time.h>
#include <LiquidCrystal_I2C.h>

// ----- SHT31 -----
#include "Adafruit_SHT31.h"

// ----- AS7331 -----
#include "AS7331.h"

// ----- BME/BMP280 -----
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_BMP280.h>

// ----- INA219 -----
#include <Adafruit_INA219.h>

// ----- microSD (SdFat) -----
#include <SPI.h>
#include <SdFat.h>

// ---------- SPI pins for SD ----------
#define SD_CS   1
#define SD_MOSI 9
#define SD_MISO 8
#define SD_SCK  7

// ---------- I2C addresses ----------
#define SHT31_ADDR_1 0x44
#define SHT31_ADDR_2 0x45
#define AS7331_I2C_ADDRESS 0x74

// ---------- WiFi ----------
const char* ssid     = "xxxxxxxxxx";
const char* password = "xxxxxxxxxx";

// ---------- Objects ----------
Adafruit_SHT31 sht1 = Adafruit_SHT31();
Adafruit_SHT31 sht2 = Adafruit_SHT31();
AS7331 uv(AS7331_I2C_ADDRESS);
Adafruit_BME280 bme;
Adafruit_BMP280 bmp;
Adafruit_INA219 ina219;

// Dirección típica del módulo I2C: 0x27 o 0x3F
LiquidCrystal_I2C lcd(0x27, 20, 4);

SdFat sd;
SdFile file;

// ---------- Flags ----------
bool haveSHT1 = false, haveSHT2 = false, haveUV = false;
bool haveBME = false, haveBMP = false;
bool haveINA = false;

// ---------- Energy and overcurrent ----------
float energy_mWh = 0.0;
uint32_t lastEnergyUpdate = 0;
const float OVERCURRENT_THRESHOLD_mA = 1500.0;  // Ajusta según tu sistema
bool overCurrent = false;

// Promedio de lecturas INA219
const uint8_t INA_SAMPLES = 10;  // Ajustable: 5, 10, 20...


// ---------- Get datetime ISO8601 ----------
String getDateTimeString() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return "1970-01-01T00:00:00";
  }
  char buffer[25];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &timeinfo);
  return String(buffer);
}

// ---------- Init SD ----------
bool initSD() {
  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);

  if (!sd.begin(SdSpiConfig(SD_CS, SHARED_SPI, SD_SCK_MHZ(25)))) {
    Serial.println(F("SD init failed."));
    sd.printSdError(&Serial);
    return false;
  }

  if (!sd.exists("datos.csv")) {
    if (file.open("datos.csv", O_CREAT | O_WRITE)) {
      file.println(F("datetime_iso8601,timestamp_ms,sht1_T_C,sht1_RH_pct,sht2_T_C,sht2_RH_pct,uvA,uvB,uvC,env_T_C,env_P_hPa,env_RH_pct,ina_Vbus,ina_current_mA,ina_power_mW,energy_mWh,overcurrent_flag,sensor_ok_flags"));
      file.close();
      Serial.println(F("Created datos.csv with header."));
    } else {
      Serial.println(F("Failed to create datos.csv"));
      return false;
    }
  }
  return true;
}

// ---------- Append CSV ----------
void appendCSV(String datetime, uint32_t t_ms,
               float sht1T, float sht1RH,
               float sht2T, float sht2RH,
               float uvA, float uvB, float uvC,
               float envT, float envP_hPa, float envRH,
               float inaV, float inaI, float inaP,
               float energy_mWh, bool overCurrent,
               uint16_t okFlags) {

  if (file.open("datos.csv", O_WRITE | O_APPEND)) {

    file.print(datetime); file.print(',');
    file.print(t_ms); file.print(',');

    file.print(isnan(sht1T) ? NAN : sht1T, 2); file.print(',');
    file.print(isnan(sht1RH) ? NAN : sht1RH, 2); file.print(',');
    file.print(isnan(sht2T) ? NAN : sht2T, 2); file.print(',');
    file.print(isnan(sht2RH) ? NAN : sht2RH, 2); file.print(',');
    file.print(isnan(uvA) ? NAN : uvA, 3); file.print(',');
    file.print(isnan(uvB) ? NAN : uvB, 3); file.print(',');
    file.print(isnan(uvC) ? NAN : uvC, 3); file.print(',');
    file.print(isnan(envT) ? NAN : envT, 2); file.print(',');
    file.print(isnan(envP_hPa) ? NAN : envP_hPa, 2); file.print(',');
    file.print(isnan(envRH) ? NAN : envRH, 2); file.print(',');

    file.print(isnan(inaV) ? NAN : inaV, 3); file.print(',');
    file.print(isnan(inaI) ? NAN : inaI, 3); file.print(',');
    file.print(isnan(inaP) ? NAN : inaP, 3); file.print(',');

    file.print(energy_mWh, 3); file.print(',');
    file.print(overCurrent ? 1 : 0); file.print(',');

    file.println(okFlags);

    file.close();
  } else {
    Serial.println(F("Error opening datos.csv for append."));
    sd.printSdError(&Serial);
  }
}

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  Serial.println(F("\nMulti-sensor Logger - HEMS Project"));

  // ---- LCD ----
  lcd.init();        // Inicializa la pantalla
  lcd.backlight();   // Enciende la retroiluminación
  lcd.setCursor(0,0);
  lcd.print("Bienvenido");   // Mensaje fijo en la primera línea

  // ---- WiFi ----
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");

  // ---- NTP ----
  configTime(-6 * 3600, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Waiting for NTP time");
  time_t nowSec = time(nullptr);
  while (nowSec < 1700000000) {
    delay(200);
    Serial.print(".");
    nowSec = time(nullptr);
  }
  Serial.println("\nTime synchronized!");

  Wire.begin();

  // ---- SHT31 #1 ----
  haveSHT1 = sht1.begin(SHT31_ADDR_1);
  if (haveSHT1) {
    sht1.heater(false);
    Serial.println(F("SHT31 #1 OK (0x44)."));
  } else {
    Serial.println(F("SHT31 #1 NOT found."));
  }

  // ---- SHT31 #2 ----
  haveSHT2 = sht2.begin(SHT31_ADDR_2);
  if (haveSHT2) {
    sht2.heater(false);
    Serial.println(F("SHT31 #2 OK (0x45)."));
  } else {
    Serial.println(F("SHT31 #2 NOT found."));
  }

  // ---- AS7331 UV ----
  haveUV = uv.begin();
  if (haveUV) {
    uv.powerUp();
    uv.setConversionTime(AS7331_CONV_1024);
    uv.startMeasurement();
    Serial.println(F("AS7331 UV OK."));
  } else {
    Serial.println(F("AS7331 UV NOT found."));
  }

  // ---- BME/BMP ----
  if (bme.begin(0x76) || bme.begin(0x77)) {
    haveBME = true;
    Serial.println(F("BME280 OK."));
  } else if (bmp.begin(0x76) || bmp.begin(0x77)) {
    haveBMP = true;
    Serial.println(F("BMP280 OK."));
  } else {
    Serial.println(F("BME/BMP NOT found."));
  }

  // ---- INA219 ----
  haveINA = ina219.begin();
  if (haveINA) {
    Serial.println(F("INA219 OK."));
    ina219.setCalibration_32V_2A();  // Para módulo Elegoo con shunt 0.1 ohm
  } else {
    Serial.println(F("INA219 NOT found."));
  }

  // ---- SD ----
  initSD();

  lastEnergyUpdate = millis();
}

uint32_t lastPrint = 0;
const uint32_t LOG_PERIOD_MS = 1000;

// ---------- Loop ----------
void loop() {
  uint32_t now = millis();
  if (now - lastPrint < LOG_PERIOD_MS) return;
  lastPrint = now;

  String datetime = getDateTimeString();

  // ---- SHT31 #1 ----
  float sht1T = NAN, sht1RH = NAN;
  bool sht1OK = false;
  if (haveSHT1) {
    sht1T = sht1.readTemperature();
    sht1RH = sht1.readHumidity();
    sht1OK = (!isnan(sht1T) && !isnan(sht1RH));
  }

  // Mostrar en LCD
  lcd.setCursor(0,1);   // Segunda línea
  lcd.print("Temperatura: ");
  lcd.print(sht1T, 2);  // Imprime con 2 decimales
  lcd.print(" C");

  // ---- SHT31 #2 ----
  float sht2T = NAN, sht2RH = NAN;
  bool sht2OK = false;
  if (haveSHT2) {
    sht2T = sht2.readTemperature();
    sht2RH = sht2.readHumidity();
    sht2OK = (!isnan(sht2T) && !isnan(sht2RH));
  }

  // ---- AS7331 UV ----
  float uvA = NAN, uvB = NAN, uvC = NAN;
  bool uvOK = false;
  if (haveUV) {
    bool ready = false;
    uint32_t start = millis();
    while (!ready && (millis() - start < 400)) {
      if (uv.conversionReady()) ready = true;
      else delay(5);
    }
    if (ready) {
      uvA = uv.getUVA_uW();
      uvB = uv.getUVB_uW();
      uvC = uv.getUVC_uW();
      uvOK = true;
      uv.startMeasurement();
    }
  }

  // ---- BME/BMP ----
  float envT = NAN, envP_hPa = NAN, envRH = NAN;
  bool envOK = false;
  if (haveBME) {
    envT = bme.readTemperature();
    envP_hPa = bme.readPressure() / 100.0f;
    envRH = bme.readHumidity();
    envOK = true;
  } else if (haveBMP) {
    envT = bmp.readTemperature();
    envP_hPa = bmp.readPressure() / 100.0f;
    envRH = NAN;
    envOK = true;
  }

  // ---- INA219 ----
// ---- INA219 (promediado) ----
float inaV = NAN, inaI = NAN, inaP = NAN;
bool inaOK = false;

if (haveINA) {

  float sumV = 0, sumI = 0, sumP = 0;

  for (uint8_t i = 0; i < INA_SAMPLES; i++) {
    float v = ina219.getBusVoltage_V();
    float i_mA = ina219.getCurrent_mA();
    float p_mW = v * (i_mA / 1000.0) * 1000.0;

    sumV += v;
    sumI += i_mA;
    sumP += p_mW;

    delay(2);  // Pequeño delay para estabilidad
  }

  inaV = sumV / INA_SAMPLES;
  inaI = sumI / INA_SAMPLES;
  inaP = sumP / INA_SAMPLES;

  inaOK = true;

  // ---- Detección de sobrecorriente ----
  overCurrent = (inaI > OVERCURRENT_THRESHOLD_mA);

  // ---- Energía acumulada ----
  uint32_t nowEnergy = millis();
  if (lastEnergyUpdate > 0) {
    float dt_hours = (nowEnergy - lastEnergyUpdate) / 3600000.0;
    energy_mWh += inaP * dt_hours;
  }
  lastEnergyUpdate = nowEnergy;
}

  // ---- Flags ----
  uint16_t okFlags = 0;
  if (sht1OK) okFlags |= (1 << 0);
  if (sht2OK) okFlags |= (1 << 1);
  if (uvOK)   okFlags |= (1 << 2);
  if (envOK)  okFlags |= (1 << 3);
  if (inaOK)  okFlags |= (1 << 4);

  // ---- Serial print ----
  Serial.print(datetime); Serial.print(',');
  Serial.print(now);      Serial.print(',');
  Serial.print(sht1T);    Serial.print(',');
  Serial.print(sht1RH);   Serial.print(',');
  Serial.print(sht2T);    Serial.print(',');
  Serial.print(sht2RH);   Serial.print(',');
  Serial.print(uvA);      Serial.print(',');
  Serial.print(uvB);      Serial.print(',');
  Serial.print(uvC);      Serial.print(',');
  Serial.print(envT);     Serial.print(',');
  Serial.print(envP_hPa); Serial.print(',');
  Serial.print(envRH);    Serial.print(',');
  Serial.print(inaV);     Serial.print(',');
  Serial.print(inaI);     Serial.print(',');
  Serial.print(inaP);     Serial.print(',');
  Serial.print(energy_mWh); Serial.print(',');
  Serial.print(overCurrent ? 1 : 0); Serial.print(',');
  Serial.println(okFlags);

  // ---- Save to SD ----
  appendCSV(datetime, now,
            sht1T, sht1RH,
            sht2T, sht2RH,
            uvA, uvB, uvC,
            envT, envP_hPa, envRH,
            inaV, inaI, inaP,
            energy_mWh, overCurrent,
            okFlags);
}
