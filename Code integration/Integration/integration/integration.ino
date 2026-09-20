#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <time.h>
#include <I2C_LCD.h>
#include <ThingSpeak.h>
#include <Adafruit_SHT31.h>
#include <AS7331.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_BMP280.h>
#include <INA219.h>
#include <SPI.h>
#include <SdFat.h>

#define TINY_GSM_MODEM_SIM7600
#include <TinyGsmClient.h>

// --- 4G LTE ---
#define MODEM_TX 43
#define MODEM_RX 44
#define SerialAT Serial1

#define USE_SIM7600 false //

// ---------- Config WiFi ----------
String ssid     = "LaboratorioDelta";
String password = "labdelta21!";

TinyGsm modem(SerialAT);
TinyGsmClient gsmClient(modem);

const char apn[]  = "internet.ideasclaro";  // tu APN
const char user[] = "";
const char pass[] = "";

// --- WiFi ---
WiFiClient wifiClient;

// --- Cliente activo ---
Client* activeClient = nullptr;

unsigned long myChannelNumber = 3355700;
const char * myWriteAPIKey = "W1Y7D3C7TBU7BN4Y";

// ---------- Definiciones de hardware ----------

// Pines SPI para SD
#define MOSI_PIN 10
#define MISO_PIN 9
#define SCK_PIN  8
#define SD_CS    2   // Chip Select de la SD

// Direcciones I2C de sensores
#define SHT31_ADDR_1 0x44
#define SHT31_ADDR_2 0x45
#define AS7331_ADDR  0x74
#define BM_ADDR_1   0x76 //Para BME280 o BMP280
#define BM_ADDR_2   0x77 //Para BME280 o BMP280, en caso de usar dos, con la segunda opción de direccón física de I2C
#define INA219_ADDR  0x40
#define INA219_ADDR_2  0x41
#define LCD_ADDR 0x27

#define LED_BUILTIN 21   // En la mayoría de placas ESP32 el LED está en GPIO2

// Umbral de sobrecorriente
const float OVERCURRENT_THRESHOLD_mA = 1500.0;

// ---------- Flags de disponibilidad de sensores ----------
bool haveSHT1  = false;
bool haveSHT2  = false;
bool haveUV    = false;
bool haveBME   = false;
bool haveBMP   = false;
bool haveINA   = false;
bool haveINA_2 = false;
bool haveSD    = false;
bool haveLCD   = false;
bool wifi_disp = false;

// ---------- Variables auxiliares ----------
uint32_t lastEnergyUpdate = 0;

// ---------- Objetos ----------
// La dirección I2C se asigna en el begin(), dentro de Setup
Adafruit_SHT31 sht1 = Adafruit_SHT31();
Adafruit_SHT31 sht2 = Adafruit_SHT31();
AS7331 uv(AS7331_ADDR);
Adafruit_BME280 bme;
Adafruit_BMP280 bmp;
INA219 ina219(INA219_ADDR);
INA219 ina219_wind(INA219_ADDR_2);
I2C_LCD lcd(LCD_ADDR);  // Dirección, columnas, filas
SdFat sd;
SdFile file;

#define WIFI_RETRY_TIMEOUT 10000   // 10 segundos
#define NTP_RETRY_TIMEOUT 10000    // 10 segundos

// Coeficientes de calibración (pendiente y offset)
float cal_sht1T_m = 1.0, cal_sht1T_b = 0.0;
float cal_sht1RH_m = 1.0, cal_sht1RH_b = 0.0;

float cal_sht2T_m = 1.0, cal_sht2T_b = 0.0;
float cal_sht2RH_m = 1.0, cal_sht2RH_b = 0.0;

float cal_envT_m = 1.0, cal_envT_b = 0.0;
float cal_envP_m = 1.0, cal_envP_b = 0.0;
float cal_envRH_m = 1.0, cal_envRH_b = 0.0;

float cal_inaV_m = 1.0, cal_inaV_b = 0.0;
float cal_inaI_m = 1.0, cal_inaI_b = 0.0;

float cal_inaV_wind_m = 1.0, cal_inaV_wind_b = 0.0;
float cal_inaI_wind_m = 1.0, cal_inaI_wind_b = 0.0;

float cal_uvA_m = 1.0, cal_uvA_b = 0.0;
float cal_uvB_m = 1.0, cal_uvB_b = 0.0;
float cal_uvC_m = 1.0, cal_uvC_b = 0.0;

// ---------- Variables globales compartidas ----------
float   g_sht1T, g_sht1RH, g_sht2T, g_sht2RH;
float   g_uvA, g_uvB, g_uvC;
float   g_envT, g_envP, g_envRH;
float   g_inaV, g_inaI, g_inaP;
float   g_inaV_wind, g_inaI_wind, g_inaP_wind;
float   g_energy_mWh = 0.0;
bool    g_overCurrent = false;
bool    g_overCurrent_wind = false;
uint16_t  g_okFlags = 0;
String    g_datetime;

// ---------- Semáforo ----------
SemaphoreHandle_t xDataSemaphore;

// ---------- Funciones ----------
String getDateTimeString() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return "1970-01-01T00:00:00";
  char buffer[25];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &timeinfo);
  return String(buffer);
}

bool initSD() {
  SPI.begin(MOSI_PIN, MISO_PIN, SCK_PIN, SD_CS);
  if (!sd.begin(SdSpiConfig(SD_CS, SHARED_SPI, SD_SCK_MHZ(25)))) return false;
  if (!sd.exists("datos.csv")) {
    if (file.open("datos.csv", O_CREAT | O_WRITE)) {
      file.println(F("datetime_iso8601,timestamp_ms,sht1_T_C,sht1_RH_pct,sht2_T_C,sht2_RH_pct,uvA,uvB,uvC,env_T_C,env_P_hPa,env_RH_pct,ina_Vbus,ina_current_mA,ina_power_mW,energy_mWh,overcurrent_flag,sensor_ok_flags"));
      file.close();
    }
  }
  haveSD=true;
  return true;
}

void appendCSV() {
  if (file.open("datos.csv", O_WRITE | O_APPEND)) {
    file.print(g_datetime); file.print(',');
    file.print(millis()); file.print(',');
    file.print(g_sht1T, 2); file.print(',');
    file.print(g_sht1RH, 2); file.print(',');
    file.print(g_sht2T, 2); file.print(',');
    file.print(g_sht2RH, 2); file.print(',');
    file.print(g_uvA, 3); file.print(',');
    file.print(g_uvB, 3); file.print(',');
    file.print(g_uvC, 3); file.print(',');
    file.print(g_envT, 2); file.print(',');
    file.print(g_envP, 2); file.print(',');
    file.print(g_envRH, 2); file.print(',');
    file.print(g_inaV_wind, 3); file.print(',');
    file.print(g_inaI_wind, 3); file.print(',');
    file.print(g_inaP_wind, 3); file.print(',');
    file.print(g_overCurrent_wind ? 1 : 0); file.print(',');
    file.print(g_inaV, 3); file.print(',');
    file.print(g_inaI, 3); file.print(',');
    file.print(g_inaP, 3); file.print(',');
    file.print(g_energy_mWh, 3); file.print(',');
    file.print(g_overCurrent ? 1 : 0); file.print(',');
    file.println(g_okFlags);
    file.close();
  }
}

#define BATCH_SIZE 10
String bufferSD = "";
int lineCountSD = 0;

void appendCSVBatch() {
  String line = "";
  line += g_datetime + ",";
  line += String(millis()) + ",";
  line += String(g_sht1T, 2) + ",";
  line += String(g_sht1RH, 2) + ",";
  line += String(g_sht2T, 2) + ",";
  line += String(g_sht2RH, 2) + ",";
  line += String(g_uvA, 3) + ",";
  line += String(g_uvB, 3) + ",";
  line += String(g_uvC, 3) + ",";
  line += String(g_envT, 2) + ",";
  line += String(g_envP, 2) + ",";
  line += String(g_envRH, 2) + ",";
  line += String(g_inaV_wind, 3) + ",";
  line += String(g_inaI_wind, 3) + ",";
  line += String(g_inaP_wind, 3) + ",";
  line += String(g_overCurrent_wind ? 1 : 0) + ",";
  line += String(g_inaV, 3) + ",";
  line += String(g_inaI, 3) + ",";
  line += String(g_inaP, 3) + ",";
  line += String(g_energy_mWh, 3) + ",";
  line += String(g_overCurrent ? 1 : 0) + ",";
  line += String(g_okFlags);

  bufferSD += line + "\n";
  lineCountSD++;

  if (lineCountSD >= BATCH_SIZE) {
    if (file.open("datos.csv", O_WRITE | O_APPEND)) {
      file.print(bufferSD);
      file.close();
    }
    bufferSD = "";
    lineCountSD = 0;
  }
}

float avg(float *buf) {
  float sum = 0;
  for (int i=0; i<BATCH_SIZE; i++) sum += buf[i];
  return sum / BATCH_SIZE;
}

String floatToHex(float valor, int escala = 100) {
  
  if (isnan(valor)){
    valor = 0.0;
  }
  
  int entero = (int)(valor * escala);   // Escala para conservar decimales
  char buffer[10];
  sprintf(buffer, "%X", entero);        // Convierte a HEX
  return String(buffer);
}

// ---- CRC16 (polinomio 0x8005, inicial 0xFFFF) ----
uint16_t crc16(const uint8_t *data, size_t length) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < length; i++) {
    crc ^= (uint16_t)data[i] << 8;
    for (uint8_t j = 0; j < 8; j++) {
      if (crc & 0x8000) {
        crc = (crc << 1) ^ 0x8005;
      } else {
        crc <<= 1;
      }
    }
  }
  return crc;
}

String dateTimeToHex(String datetime) {
  // datetime en formato "YYYY-MM-DDTHH:MM:SS"
  int year   = datetime.substring(0,4).toInt();
  int month  = datetime.substring(5,7).toInt();
  int day    = datetime.substring(8,10).toInt();
  int hour   = datetime.substring(11,13).toInt();
  int minute = datetime.substring(14,16).toInt();
  int second = datetime.substring(17,19).toInt();

  char buffer[50];
  // Concatenar todo en HEX continuo
  sprintf(buffer, "%04X%02X%02X%02X%02X%02X", year, month, day, hour, minute, second);
  return String(buffer);
}

// Buffers para acumular lecturas
float buf_sht1T[BATCH_SIZE], buf_sht1RH[BATCH_SIZE];
float buf_sht2T[BATCH_SIZE], buf_sht2RH[BATCH_SIZE];
float buf_uvA[BATCH_SIZE], buf_uvB[BATCH_SIZE], buf_uvC[BATCH_SIZE];
float buf_envT[BATCH_SIZE], buf_envP[BATCH_SIZE], buf_envRH[BATCH_SIZE];
float buf_inaV_wind[BATCH_SIZE], buf_inaI_wind[BATCH_SIZE], buf_inaP_wind[BATCH_SIZE];
float buf_inaV[BATCH_SIZE], buf_inaI[BATCH_SIZE], buf_inaP[BATCH_SIZE];
float buf_energy[BATCH_SIZE];

int sampleIndex = 0;

void addSample() {
  buf_sht1T[sampleIndex] = g_sht1T;
  buf_sht1RH[sampleIndex] = g_sht1RH;
  buf_sht2T[sampleIndex] = g_sht2T;
  buf_sht2RH[sampleIndex] = g_sht2RH;
  buf_uvA[sampleIndex] = g_uvA;
  buf_uvB[sampleIndex] = g_uvB;
  buf_uvC[sampleIndex] = g_uvC;
  buf_envT[sampleIndex] = g_envT;
  buf_envP[sampleIndex] = g_envP;
  buf_envRH[sampleIndex] = g_envRH;
  buf_inaV_wind[sampleIndex] = g_inaV;
  buf_inaI_wind[sampleIndex] = g_inaI;
  buf_inaP_wind[sampleIndex] = g_inaP;
  buf_inaV[sampleIndex] = g_inaV;
  buf_inaI[sampleIndex] = g_inaI;
  buf_inaP[sampleIndex] = g_inaP;
  buf_energy[sampleIndex] = g_energy_mWh;

  sampleIndex++;

  if (sampleIndex >= BATCH_SIZE) {
    sendAveragesToThingSpeak();
    sampleIndex = 0; // reinicia
  }
}

void sendAveragesToThingSpeak(){

// --- Codificación HEX + CRC ---

  String payloadHex =
    dateTimeToHex(g_datetime) + "," +
    floatToHex(avg(buf_sht1T), 100) + "," + floatToHex(avg(buf_sht1RH), 100) + "," +
    floatToHex(avg(buf_sht2T), 100) + "," + floatToHex(avg(buf_sht2RH), 100) + "," +
    floatToHex(avg(buf_uvA), 1000) + "," + floatToHex(avg(buf_uvB), 1000) + "," + floatToHex(avg(buf_uvC), 1000) + "," +
    floatToHex(avg(buf_envT), 100) + "," + floatToHex(avg(buf_envP), 10) + "," + floatToHex(avg(buf_envRH), 100) + "," +
    floatToHex(avg(buf_inaV_wind), 100) + "," + floatToHex(avg(buf_inaI_wind), 10) + "," + floatToHex(avg(buf_inaP_wind), 10) + "," +
    floatToHex(avg(buf_inaV), 100) + "," + floatToHex(avg(buf_inaI), 10) + "," + floatToHex(avg(buf_inaP), 10) + "," +
    floatToHex(avg(buf_energy), 100) + "," +
    floatToHex(g_overCurrent, 1) + "," + floatToHex(g_okFlags, 1);

  uint16_t crc = crc16((const uint8_t*)payloadHex.c_str(), payloadHex.length());
  char crcBuffer[10];
  sprintf(crcBuffer, "%04X", crc);
  String payloadFinal = payloadHex + ",CRC:" + String(crcBuffer);
  
  // --- Enviar a ThingSpeak ---
  if (activeClient != nullptr) {
    ThingSpeak.setField(8, payloadFinal);
    int httpCode = ThingSpeak.writeFields(myChannelNumber, myWriteAPIKey);
    if (httpCode == 200) {
      Serial.println("Channel write successful.");
      Serial.println(payloadFinal);
    } else {
      Serial.println("Problem writing to channel. HTTP error code " + String(httpCode));
    }
  }

}

void loadCalibration() {
  if (sd.exists("ajuste.csv")) {
    if (file.open("ajuste.csv", O_READ)) {
      char line[64];
      while (file.fgets(line, sizeof(line))) {
        String s(line);
        s.trim();
        if (s.length() == 0 || s.startsWith("sensor")) continue; // saltar encabezado

        int c1 = s.indexOf(',');
        int c2 = s.indexOf(',', c1+1);
        if (c1 < 0 || c2 < 0) continue;

        String sensor = s.substring(0, c1);
        float m = s.substring(c1+1, c2).toFloat();
        float b = s.substring(c2+1).toFloat();

        if (sensor == "sht1T") { cal_sht1T_m = m; cal_sht1T_b = b; }
        else if (sensor == "sht1RH") { cal_sht1RH_m = m; cal_sht1RH_b = b; }
        else if (sensor == "sht2T") { cal_sht2T_m = m; cal_sht2T_b = b; }
        else if (sensor == "sht2RH") { cal_sht2RH_m = m; cal_sht2RH_b = b; }
        else if (sensor == "envT") { cal_envT_m = m; cal_envT_b = b; }
        else if (sensor == "envP") { cal_envP_m = m; cal_envP_b = b; }
        else if (sensor == "envRH") { cal_envRH_m = m; cal_envRH_b = b; }
        else if (sensor == "inaV") { cal_inaV_m = m; cal_inaV_b = b; }
        else if (sensor == "inaI") { cal_inaI_m = m; cal_inaI_b = b; }
        else if (sensor == "inaV_wind") { cal_inaV_wind_m = m; cal_inaV_b = b; }
        else if (sensor == "inaI_wind") { cal_inaI_wind_m = m; cal_inaI_b = b; }
        else if (sensor == "uvA") { cal_uvA_m = m; cal_uvA_b = b; }
        else if (sensor == "uvB") { cal_uvB_m = m; cal_uvB_b = b; }
        else if (sensor == "uvC") { cal_uvC_m = m; cal_uvC_b = b; }
      }
      file.close();
      Serial.println(F("✅ Factores de ajuste cargados desde calib.csv"));
    }
  } else {
    Serial.println(F("⚠️ No se encontró calib.csv, usando valores por defecto"));
  }
}

float ajuste(float raw, float m, float b) {
  if (isnan(raw)) return NAN;
  return raw * m + b;
}

// ---- Lectura con repetibilidad ----
float readAverage( std::function<float()> readFunc, uint8_t samples = 3 ) {
  float sum = 0;
  for (uint8_t i = 0; i < samples; i++) {
    sum += readFunc();
    delay(5);
  }
  return sum / samples;
}

void ntpInit(){
    configTime(-6 * 3600, 0, "pool.ntp.org", "time.nist.gov");
    Serial.print("Re-sincronizando NTP...");
    time_t nowSec = time(nullptr);
    unsigned long ntpStart = millis();
    while (nowSec < 1700000000 && (millis() - ntpStart < NTP_RETRY_TIMEOUT)) {
      delay(200);
      Serial.print(".");
      nowSec = time(nullptr);
    }
    if (nowSec >= 1700000000) {
      Serial.println("\n✅ Hora NTP sincronizada!");
    } else {
      Serial.println("\n⚠️ No se pudo sincronizar NTP en este ciclo.");
    }
}

void enviarAT(String comando, uint32_t espera) {
  Serial.println("------------------------------------------------");
  Serial.print("AT> ");
  Serial.println(comando);

  while (SerialAT.available())
    SerialAT.read();

  SerialAT.println(comando);

  uint32_t inicio = millis();

  while ((millis() - inicio) < espera)
  {
    while (SerialAT.available())
    {
      Serial.write(SerialAT.read());
    }
  }

  Serial.println();
}

void simInit(){

  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);
  delay(3000);

  Serial.println("Configurando SIM7600...");

  enviarAT("AT", 1000);
  enviarAT("AT+CPIN?", 2000);
  enviarAT("AT+CSQ", 1000);
  enviarAT("AT+CREG?", 1000);

  enviarAT("AT+CGDCONT=1,\"IP\",\"internet.ideasclaro\"", 2000);

  // Red automática LTE/3G/2G
  enviarAT("AT+CNMP=2", 2000);

  // Abrir servicio de datos
  enviarAT("AT+NETOPEN", 5000);

  // Consultar IP
  enviarAT("AT+IPADDR", 2000);

  // -------------------------------
  // Inicializar TinyGSM
  // -------------------------------
  Serial.println("Inicializando TinyGSM...");

  if (!modem.init()) {
    Serial.println("❌ Error inicializando módem");
    return;
  }

  Serial.println("Módem inicializado");

  // Información del módem
  String modemInfo = modem.getModemInfo();

  Serial.print("Modem: ");
  Serial.println(modemInfo);

  Serial.println("Esperando registro en red...");

  if (!modem.waitForNetwork(120000L)) {
    Serial.println("❌ Sin red celular");
    return;
  }

  Serial.println("Conectando datos móviles...");

  if (!modem.gprsConnect(apn, user, pass)) {
    Serial.println("❌ No se pudo conectar a Internet");
    return;
  }

  Serial.print("Estado GPRS: ");
  Serial.println(modem.isGprsConnected());

  Serial.println("Internet conectado");

  Serial.print("IP: ");
  Serial.println(modem.localIP());

  activeClient = &gsmClient;

  if (activeClient != nullptr) {
    ThingSpeak.begin(*activeClient);
    Serial.println("✅ Conectado por SIM7600");
    ntpInit();
  } else {
    Serial.println("❌ Cliente no inicializado, no se puede enviar a ThingSpeak");
  }

}

void loadWiFiConfig() {
  if (sd.exists("wifi.cfg")) {
    if (file.open("wifi.cfg", O_READ)) {
      char line[64];
      while (file.fgets(line, sizeof(line))) {
        String s(line);
        s.trim();
        if (s.startsWith("SSID=")) ssid = s.substring(5);
        else if (s.startsWith("PASS=")) password = s.substring(5);
      }
      file.close();
      Serial.println("✅ Configuración WiFi cargada desde wifi.cfg");
    }
  } else {
    Serial.println("⚠️ No se encontró wifi.cfg, se usará configuración manual");
  }
}

void saveWiFiConfig(String ssid_1, String pass) {
  if (file.open("wifi.cfg", O_WRITE | O_CREAT | O_TRUNC)) {
    file.print("SSID="); file.println(ssid_1);
    file.print("PASS="); file.println(pass);
    file.close();
    Serial.println("✅ Configuración WiFi guardada en wifi.cfg");
  } else {
    Serial.println("❌ Error al guardar wifi.cfg");
  }
}

// ---- Intento de reconexión WiFi ----
bool WiFi_init() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado. Intentando reconectar...");
    WiFi.begin(ssid.c_str(), password.c_str());

    unsigned long startAttempt = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - startAttempt < WIFI_RETRY_TIMEOUT)) {
      delay(500);
      Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\n✅ Reconectado a WiFi."); 
      activeClient = &wifiClient;
      ThingSpeak.begin(*activeClient);
      ntpInit();
      return true;
    } else {
      Serial.println("\n❌ No se pudo reconectar en este ciclo.");
      return false;
    }
  }
}

void saveCalibration() {
  if (file.open("ajuste.csv", O_WRITE | O_CREAT | O_TRUNC)) {
    file.println("sensor,m,b");
    file.print("sht1T,"); file.print(cal_sht1T_m); file.print(","); file.println(cal_sht1T_b);
    file.print("sht1RH,"); file.print(cal_sht1RH_m); file.print(","); file.println(cal_sht1RH_b);
    file.print("sht2T,"); file.print(cal_sht2T_m); file.print(","); file.println(cal_sht2T_b);
    file.print("sht2RH,"); file.print(cal_sht2RH_m); file.print(","); file.println(cal_sht2RH_b);
    file.print("envT,"); file.print(cal_envT_m); file.print(","); file.println(cal_envT_b);
    file.print("envP,"); file.print(cal_envP_m); file.print(","); file.println(cal_envP_b);
    file.print("envRH,"); file.print(cal_envRH_m); file.print(","); file.println(cal_envRH_b);
    file.print("inaV,"); file.print(cal_inaV_m); file.print(","); file.println(cal_inaV_b);
    file.print("inaI,"); file.print(cal_inaI_m); file.print(","); file.println(cal_inaI_b);
    file.print("inaV_wind,"); file.print(cal_inaV_wind_m); file.print(","); file.println(cal_inaV_b);
    file.print("inaI_wind,"); file.print(cal_inaI_wind_m); file.print(","); file.println(cal_inaI_b);
    file.print("uvA,"); file.print(cal_uvA_m); file.print(","); file.println(cal_uvA_b);
    file.print("uvB,"); file.print(cal_uvB_m); file.print(","); file.println(cal_uvB_b);
    file.print("uvC,"); file.print(cal_uvC_m); file.print(","); file.println(cal_uvC_b);
    file.close();
    Serial.println(F("✅ Calibración guardada en calib.csv"));
  } else {
    Serial.println(F("❌ Error al guardar calib.csv"));
  }
}

// ---- Inicio de sensores y tarjeta SD ----

void init() {

  Serial.println(F("Iniciando hardware ..."));
  
  if (!haveSD){
    Serial.println(F("Inicializando SD..."));
    haveSD=initSD();
    Serial.println(F("SD lista"));
    }
  
  if (!haveSHT1) {
    Serial.println(F("Iniciando SHT31 #1..."));
    haveSHT1 = sht1.begin(SHT31_ADDR_1);
  }
  
  if (!haveSHT2) {
    Serial.println(F("Iniciando SHT31 #2..."));
    haveSHT2 = sht2.begin(SHT31_ADDR_2);
  }
  
  if (!haveUV) {
    Serial.println(F("Iniciando AS7331..."));
    haveUV = uv.begin();
    if (haveUV) {
      uv.powerUp();
      uv.setConversionTime(AS7331_CONV_1024);
      uv.startMeasurement();
    }
  }

  if (!haveBME && !haveBMP) {
    Serial.println(F("Iniciando BME/BMP..."));
    if (bme.begin(BM_ADDR_1) || bme.begin(BM_ADDR_2)) haveBME = true;
    else if (bmp.begin(BM_ADDR_1) || bmp.begin(BM_ADDR_1)) haveBMP = true;
  } //Considera un solo BMP o BME, si hay dos, se puede actualizar esta parte.

  if (!haveINA) {
    Serial.println(F("Iniciando INA219..."));
    haveINA = ina219.begin();
    //if (haveINA) ina219.setCalibration_32V_2A();
  }

    if (!haveINA_2) {
    Serial.println(F("Iniciando INA219 2..."));
    haveINA_2 = ina219_wind.begin();
    //if (haveINA_2) ina219_wind.setCalibration_32V_2A();
  }

    if (!haveLCD) {
    Serial.println(F("Iniciando LCD"));
    lcd.begin(16, 2);   // 16 columnas, 2 filas
    lcd.backlight();    // enciende la luz de fondo si la librería lo soporta
    }

}

void taskMenu(void * parameter) {
  for (;;) {

    if (Serial.available()) {

      String cmd = Serial.readStringUntil('\n');
      cmd.trim();

      if (cmd.equalsIgnoreCase("SAVE")) {
        saveCalibration();
      } else if (cmd.equalsIgnoreCase("LOAD")) {
        loadCalibration();
      } else if (cmd.equalsIgnoreCase("SHOW")) {
        Serial.println("=== Coeficientes de calibración actuales ===");
        Serial.print("sht1T_m: "); Serial.println(cal_sht1T_m);
        Serial.print("sht1T_b: "); Serial.println(cal_sht1T_b);
        Serial.print("sht1RH_m: "); Serial.println(cal_sht1RH_m);
        Serial.print("sht1RH_b: "); Serial.println(cal_sht1RH_b);
        Serial.print("sht2T_m: "); Serial.println(cal_sht2T_m);
        Serial.print("sht2T_b: "); Serial.println(cal_sht2T_b);
        Serial.print("sht2RH_m: "); Serial.println(cal_sht2RH_m);
        Serial.print("sht2RH_b: "); Serial.println(cal_sht2RH_b);
        Serial.print("envT_m: "); Serial.println(cal_envT_m);
        Serial.print("envT_b: "); Serial.println(cal_envT_b);
        Serial.print("envP_m: "); Serial.println(cal_envP_m);
        Serial.print("envP_b: "); Serial.println(cal_envP_b);
        Serial.print("envRH_m: "); Serial.println(cal_envRH_m);
        Serial.print("envRH_b: "); Serial.println(cal_envRH_b);
        Serial.print("inaV_m: "); Serial.println(cal_inaV_m);
        Serial.print("inaV_b: "); Serial.println(cal_inaV_b);
        Serial.print("inaI_m: "); Serial.println(cal_inaI_m);
        Serial.print("inaI_b: "); Serial.println(cal_inaI_b);
        Serial.print("inaV_wind_m: "); Serial.println(cal_inaV_wind_m);
        Serial.print("inaV_wind_b: "); Serial.println(cal_inaV_b);
        Serial.print("inaI_wind_m: "); Serial.println(cal_inaI_wind_m);
        Serial.print("inaI_wind_b: "); Serial.println(cal_inaI_b);
        Serial.print("uvA_m: "); Serial.println(cal_uvA_m);
        Serial.print("uvA_b: "); Serial.println(cal_uvA_b);
        Serial.print("uvB_m: "); Serial.println(cal_uvB_m);
        Serial.print("uvB_b: "); Serial.println(cal_uvB_b);
        Serial.print("uvC_m: "); Serial.println(cal_uvC_m);
        Serial.print("uvC_b: "); Serial.println(cal_uvC_b);
        Serial.println("===========================================");
      
      } 

      else if (cmd.startsWith("SET")) {
        // Formato: SET nombre valor
        int c1 = cmd.indexOf(' ');
        int c2 = cmd.indexOf(' ', c1+1);
        if (c1 > 0 && c2 > c1) {
          String nombre = cmd.substring(c1+1, c2);
          float valor = cmd.substring(c2+1).toFloat();

          if (nombre == "sht1T_m") cal_sht1T_m = valor;
          else if (nombre == "sht1T_b") cal_sht1T_b = valor;
          else if (nombre == "sht1RH_m") cal_sht1RH_m = valor;
          else if (nombre == "sht1RH_b") cal_sht1RH_b = valor;
          else if (nombre == "sht2T_m") cal_sht2T_m = valor;
          else if (nombre == "sht2T_b") cal_sht2T_b = valor;
          else if (nombre == "sht2RH_m") cal_sht2RH_m = valor;
          else if (nombre == "sht2RH_b") cal_sht2RH_b = valor;
          else if (nombre == "envT_m") cal_envT_m = valor;
          else if (nombre == "envT_b") cal_envT_b = valor;
          else if (nombre == "envP_m") cal_envP_m = valor;
          else if (nombre == "envP_b") cal_envP_b = valor;
          else if (nombre == "envRH_m") cal_envRH_m = valor;
          else if (nombre == "envRH_b") cal_envRH_b = valor;
          else if (nombre == "inaV_m") cal_inaV_m = valor;
          else if (nombre == "inaV_b") cal_inaV_b = valor;
          else if (nombre == "inaI_m") cal_inaI_m = valor;
          else if (nombre == "inaI_b") cal_inaI_b = valor;
          else if (nombre == "inaV_wind_m") cal_inaV_wind_m = valor;
          else if (nombre == "inaV_wind_b") cal_inaV_b = valor;
          else if (nombre == "inaI_wind_m") cal_inaI_wind_m = valor;
          else if (nombre == "inaI_wind_b") cal_inaI_b = valor;
          else if (nombre == "uvA_m") cal_uvA_m = valor;
          else if (nombre == "uvA_b") cal_uvA_b = valor;
          else if (nombre == "uvB_m") cal_uvB_m = valor;
          else if (nombre == "uvB_b") cal_uvB_b = valor;
          else if (nombre == "uvC_m") cal_uvC_m = valor;
          else if (nombre == "uvC_b") cal_uvC_b = valor;

          Serial.print("Coeficiente actualizado: ");
          Serial.print(nombre);
          Serial.print(" = ");
          Serial.println(valor);
        }
      }

      else if (cmd.startsWith("SCAN")) {

        int n = WiFi.scanNetworks();

        if (n == 0) {
          Serial.println("❌ No se encontraron redes.");
        } else {
          Serial.println("✅ Redes encontradas:");
          for (int i = 0; i < n; ++i) {
            Serial.print(i + 1);
            Serial.print(": ");
            Serial.print(WiFi.SSID(i));       // Nombre de la red
            Serial.print(" (RSSI: ");
            Serial.print(WiFi.RSSI(i));       // Intensidad de señal
            Serial.print(" dBm) ");
            Serial.println((WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "Abierta" : "Segura");
            delay(10);
          }
        }

      }

      else if (cmd.startsWith("WIFI")) {
        // Formato: WIFI SSID PASSWORD
        int c1 = cmd.indexOf(' ');
        int c2 = cmd.indexOf(',', c1+1);
        if (c1 > 0 && c2 > c1) {
          ssid = cmd.substring(c1+1, c2);
          password = cmd.substring(c2+1);

          Serial.print("Intentando conectar a red: ");
          Serial.println(ssid);

          // 🔴 Apagar WiFi y limpiar estado previo
          WiFi.disconnect(true);   // desconecta y borra configuración
          delay(1000);             // pequeña pausa para estabilizar

          WiFi.begin(ssid.c_str(), password.c_str());

          unsigned long startAttempt = millis();
          while (WiFi.status() != WL_CONNECTED && (millis() - startAttempt < 15000)) {
            delay(500);
            Serial.print(".");
          }

          if (WiFi.status() == WL_CONNECTED) {
            Serial.println("\n✅ Conectado exitosamente a WiFi.");
            Serial.print("IP asignada: ");
            Serial.println(WiFi.localIP());
            activeClient = &wifiClient;
            ThingSpeak.begin(*activeClient);
            ntpInit();
            // Guardar configuración en SD
            saveWiFiConfig(ssid, password);
          } else {
            Serial.println("\n❌ No se pudo conectar a la red.");
          }
        }
      }
    } 

  vTaskDelay(1000 / portTICK_PERIOD_MS); // cada 20s

  }

}

void setup() {

  pinMode(LED_BUILTIN, OUTPUT);  // Configura el pin como salida
  Serial.begin(115200);
  Wire.begin();
  SPI.begin(MOSI_PIN, MISO_PIN, SCK_PIN, SD_CS);

  //init();
  loadCalibration();
  loadWiFiConfig();

  wifi_disp = WiFi_init();

  if (!wifi_disp){
    if (USE_SIM7600) {
      simInit();
    }
  }

  xTaskCreatePinnedToCore(taskMenu, "TaskMenu", 8192, NULL, 1, NULL, 1); // Core 0
  
  Serial.println(F("Iniciando hardware ..."));
  
  if (!haveSD){
    Serial.println(F("Inicializando SD..."));
    haveSD=initSD();
    }
  
  if (!haveSHT1) {
    Serial.println(F("Iniciando SHT31 #1..."));
    haveSHT1 = sht1.begin(SHT31_ADDR_1);
  }
  
  if (!haveSHT2) {
    Serial.println(F("Iniciando SHT31 #2..."));
    haveSHT2 = sht2.begin(SHT31_ADDR_2);
  }
  
  if (!haveUV) {
    Serial.println(F("Iniciando AS7331..."));
    haveUV = uv.begin();
    if (haveUV) {
      uv.powerUp();
      uv.setConversionTime(AS7331_CONV_1024);
      uv.startMeasurement();
    }
  }

  if (!haveBME && !haveBMP) {
    Serial.println(F("Iniciando BME/BMP..."));
    if (bme.begin(BM_ADDR_1) || bme.begin(BM_ADDR_2)) haveBME = true;
    else if (bmp.begin(BM_ADDR_1) || bmp.begin(BM_ADDR_1)) haveBMP = true;
  } //Considera un solo BMP o BME, si hay dos, se puede actualizar esta parte.

  if (!haveINA) {
    Serial.println(F("Iniciando INA219..."));
    haveINA = ina219.begin();
    //if (haveINA) ina219.setCalibration_32V_2A();
  }

  if (!haveINA_2) {
    Serial.println(F("Iniciando INA219 2..."));
    haveINA_2 = ina219_wind.begin();
    //if (haveINA_2) ina219_wind.setCalibration_32V_2A();
  }

  if (!haveLCD) {
    Serial.println(F("Iniciando LCD"));
    haveLCD=lcd.begin(16, 2);   // 16 columnas, 2 filas
    lcd.backlight();    // enciende la luz de fondo si la librería lo soporta
    lcd.print("Hola");
    Serial.println(F("LCD iniciada"));
  }
}

void loop() {
  
  digitalWrite(LED_BUILTIN, LOW);   // Enciende el LED
  delay(1000);                       // Espera 1 segundo
  digitalWrite(LED_BUILTIN, HIGH);    // Apaga el LED
  delay(1000);                       // Espera 1 segundo

  g_datetime = getDateTimeString();

  // SHT31 #1
  if (haveSHT1) {
    g_sht1T  = ajuste(readAverage([&](){ return sht1.readTemperature(); }, 3), cal_sht1T_m, cal_sht1T_b);
    g_sht1RH = ajuste(readAverage([&](){ return sht1.readHumidity(); }, 3), cal_sht1RH_m, cal_sht1RH_b);
  }

  // SHT31 #2
  if (haveSHT2) {
    g_sht2T  = ajuste(readAverage([&](){ return sht2.readTemperature(); }, 3), cal_sht2T_m, cal_sht2T_b);
    g_sht2RH = ajuste(readAverage([&](){ return sht2.readHumidity(); }, 3), cal_sht2RH_m, cal_sht2RH_b);
  }

  // AS7331 UV
  if (haveUV) {
    if (uv.conversionReady()) {
      g_uvA = ajuste(readAverage([&](){ return uv.getUVA_uW(); }, 3), cal_uvA_m, cal_uvA_b);
      g_uvB = ajuste(readAverage([&](){ return uv.getUVB_uW(); }, 3), cal_uvB_m, cal_uvB_b);
      g_uvC = ajuste(readAverage([&](){ return uv.getUVC_uW(); }, 3), cal_uvC_m, cal_uvC_b);
      uv.startMeasurement();
    }
  }

  // BME/BMP
  if (haveBME) {
    g_envT  = ajuste(readAverage([&](){ return bme.readTemperature(); }, 3), cal_envT_m, cal_envT_b);
    g_envP  = ajuste(readAverage([&](){ return bme.readPressure() / 100.0f; }, 3), cal_envP_m, cal_envP_b);
    g_envRH = ajuste(readAverage([&](){ return bme.readHumidity(); }, 3), cal_envRH_m, cal_envRH_b);

  } else if (haveBMP) {
    g_envT  = ajuste(readAverage([&](){ return bmp.readTemperature(); }, 3), cal_envT_m, cal_envT_b);
    g_envP  = ajuste(readAverage([&](){ return bmp.readPressure() / 100.0f; }, 3), cal_envP_m, cal_envP_b);
    g_envRH = NAN;
  }

  // INA219 #1
  if (haveINA) {
    g_inaV = ajuste(readAverage([&](){ return ina219.getBusVoltage_mV(); }, 3), cal_inaV_m, cal_inaV_b);
    g_inaI = ajuste(readAverage([&](){ return ina219.getCurrent_mA(); }, 3), cal_inaI_m, cal_inaI_b);
    g_inaP = g_inaV * (g_inaI / 1000.0) * 1000.0;
    g_overCurrent = (g_inaI > OVERCURRENT_THRESHOLD_mA);

    // Energía acumulada
    uint32_t nowEnergy = millis();
    if (lastEnergyUpdate > 0) {
      float dt_hours = (nowEnergy - lastEnergyUpdate) / 3600000.0;
      g_energy_mWh += g_inaP * dt_hours;
    }
    lastEnergyUpdate = nowEnergy;
  }

  // INA219 #2
  if (haveINA_2) {
    g_inaV_wind = ajuste(readAverage([&](){ return ina219_wind.getBusVoltage_mV(); }, 3), cal_inaV_wind_m, cal_inaV_b);
    g_inaI_wind = ajuste(readAverage([&](){ return ina219_wind.getCurrent_mA(); }, 3), cal_inaI_wind_m, cal_inaI_b);
    g_inaP_wind = g_inaV_wind * (g_inaI_wind / 1000.0) * 1000.0;
    g_overCurrent_wind = (g_inaI_wind > OVERCURRENT_THRESHOLD_mA);
  }
  
  if (haveLCD){
    // --- Mostrar en LCD ---
    lcd.setCursor(0,0);
    lcd.print("T: ");
    lcd.print(g_sht1T, 2);
    lcd.print(" ");
    lcd.print(char(223));
    lcd.print("C");

    lcd.setCursor(0,1);
    lcd.print("H1: ");
    lcd.print(g_sht1RH, 2);
    lcd.print(" %");

  }

  // --- Flags ---
  g_okFlags = 0;
  if (!isnan(g_sht1T) && !isnan(g_sht1RH))         g_okFlags |= (1 << 0);
  if (!isnan(g_sht2T) && !isnan(g_sht2RH))         g_okFlags |= (1 << 1);
  if (!isnan(g_uvA) && !isnan(g_uvB))              g_okFlags |= (1 << 2);
  if (!isnan(g_envT) && !isnan(g_envP))            g_okFlags |= (1 << 3);
  if (!isnan(g_inaV) && !isnan(g_inaI))            g_okFlags |= (1 << 4);
  if (!isnan(g_inaV_wind) && !isnan(g_inaI_wind))  g_okFlags |= (1 << 5);

  // --- Serial print ---
  Serial.print(g_datetime); Serial.print(',');
  Serial.print(millis());   Serial.print(',');
  Serial.print(g_sht1T);    Serial.print(',');
  Serial.print(g_sht1RH);   Serial.print(',');
  Serial.print(g_sht2T);    Serial.print(',');
  Serial.print(g_sht2RH);   Serial.print(',');
  Serial.print(g_uvA);      Serial.print(',');
  Serial.print(g_uvB);      Serial.print(',');
  Serial.print(g_uvC);      Serial.print(',');
  Serial.print(g_envT);     Serial.print(',');
  Serial.print(g_envP);     Serial.print(',');
  Serial.print(g_envRH);    Serial.print(',');
  Serial.print(g_inaV_wind);Serial.print(',');
  Serial.print(g_inaI_wind);Serial.print(',');
  Serial.print(g_inaP_wind);Serial.print(',');
  Serial.print(g_inaV);     Serial.print(',');
  Serial.print(g_inaI);     Serial.print(',');
  Serial.print(g_inaP);     Serial.print(',');
  Serial.print(g_energy_mWh); Serial.print(',');
  Serial.print(g_overCurrent ? 1 : 0); Serial.print(',');
  Serial.println(g_okFlags);


  addSample();

  // --- Guardar en SD ---
  if(haveSD){  
    appendCSVBatch();
  }
  
}