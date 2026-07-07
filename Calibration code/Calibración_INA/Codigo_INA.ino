//   FILE: INA219_calibrado_final.ino
// AUTHOR: Rob Tillaart / Potencia (PB)
// PURPOSE: Demo con calibración completa (V_Fuente, Current)

#include "INA219.h"

INA219 INA(0x40);

// --- CONSTANTES DE CALIBRACIÓN (Sustituye con tus valores de Excel) ---
float m_bus = 1.0119;    // m de Vbus
float b_bus = 0.0164;     // b de Vbus

float m_curr = 0.9913;   // m de Corriente
float b_curr = 0.9055;   // b de Corriente

float m_shunt = 1.1414;  // m de Vshunt
float b_shunt = 4.2692;  // b de Vshunt

int lecturasRestantes = 0;

void setup()
{
  Serial.begin(115200);
  Serial.println();
  Serial.println(__FILE__);
  
  Wire.begin();
  if (!INA.begin())
  {
    Serial.println("Could not connect. Fix and Reboot");
  }

  INA.setMaxCurrentShunt(3, 0.1);
  delay(1000);

  Serial.println("¡Sistema listo! Escribe 'A' y presiona Enter para tomar 10 mediciones.");
}

void loop()
{
  // =================================================================
  // --- 1. ESCUCHAR EL TECLADO (Monitor Serie) ---
  if (Serial.available() > 0)
  {
    char comando = Serial.read();
    
    // Si la tecla es 'A' mayúscula o minúscula, preparamos 10 vueltas
    if (comando == 'A' || comando == 'a')
    {
      lecturasRestantes = 10;
      Serial.println("\n>>> Iniciando bloque de 10 mediciones... <<<");
    }
  }
  // =================================================================

  // --- 2. SOLO MEDIR SI EL CONTADOR ES MAYOR A CERO ---
  if (lecturasRestantes > 0)
  {
    float sumBus = 0, sumShunt = 0, sumCurrent = 0;
    int muestras = 10;

    // 1. Realiza las 10 lecturas crudas
    for (int i = 0; i < muestras; i++)
    {
      sumBus     += INA.getBusVoltage();
      sumShunt   += INA.getShuntVoltage_mV();
      sumCurrent += INA.getCurrent_mA();
      delay(10); 
    }

    // 2. Promedios de lecturas del sensor (x)
    float vbus_m = sumBus / muestras;
    float vshunt_m = sumShunt / muestras;
    float current_m = sumCurrent / muestras;

    // --- FILTRO DE AUTORRECUPERACIÓN ---
    if (vbus_m < 0.5) 
    {
      Serial.println("--- Falso contacto detectado. Reiniciando sensor internamente... ---");
      
      Wire.begin();
      INA.begin();
      INA.setMaxCurrentShunt(3, 0.1);
      delay(200); 
      
      return; 
    }

    // 3. APLICAR LA CALIBRACIÓN (y = mx + b)
    float Vbus_a   = (m_bus * vbus_m) + b_bus;
    float Vshunt_a = (m_shunt * vshunt_m) + b_shunt;
    float Current_a = (m_curr * current_m) + b_curr;

    // --- 4. CÁLCULOS FINALES (Voltaje de Fuente y Potencia) ---
    // Convertimos Vshunt de mV a V dividiendo entre 1000 y lo sumamos a Vbus
    float V_fuente = Vbus_a + (Vshunt_a / 1000.0); 
    float Power_a  = V_fuente * Current_a; 

    // --- 5. IMPRESIÓN DE RESULTADOS LIMPIA ---
    // Ahora solo imprime exactamente lo que necesitas para tu hoja de datos
    Serial.print("Faltan: ");     Serial.print(lecturasRestantes - 1);  Serial.print(" |\t");
    Serial.print("V_FUENTE: ");   Serial.print(V_fuente, 3);            Serial.print(" V\t");
    Serial.print("CURR_A: ");     Serial.print(Current_a, 2);           Serial.print(" mA\t");
    Serial.print("PWR_A: ");      Serial.print(Power_a, 2);             Serial.println(" mW");

    lecturasRestantes--;

    if (lecturasRestantes == 0)
    {
      Serial.println(">>> Mediciones finalizadas. Presiona 'A' para repetir. <<<\n");
    }

    delay(1000); 
  }
}