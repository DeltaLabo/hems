#include <LiquidCrystal.h>

const int VT = A2;
const int DAC_output = A0;

const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;

const int btnUp = 6;
const int btnDown = 7;
const int btnOK = 8;

int ciclos = 0;
int contador = 0;
int base = 100;
int mult = 3;

float tensionVT = 0;
float tensionVC = 0;

float temperaturaVT = 0;
float temperaturaVC = 60.0;  // setpoint inicial en °C
float Tmax = 73.28 * 2.4 + 12.518;  // ≈ 188.4 °C
float delta = 0;
float Vref = 5.0;
int valorDAC = 0;

bool calentando = false;
bool modoAjuste = false;

LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

float tensionATemperatura(float V) {
  return 73.28 * V + 12.518;
}

float temperaturaATension(float T) {
  return (T - 12.518) / 73.28;
}

void setup() {
  Serial.begin(9600);
  delay(1000);

  pinMode(btnUp, INPUT_PULLUP);
  pinMode(btnDown, INPUT_PULLUP);
  pinMode(btnOK, INPUT_PULLUP);

  lcd.begin(16, 2);
  lcd.clear();
  lcd.print("Sistema listo");

  analogWriteResolution(12);

  delay(1000);
  lcd.clear();
}

void loop() {
  leerBotones();

  int medicionVT = analogRead(VT);
  tensionVT = medicionVT * 5.0 / 1023.0;

  temperaturaVT = tensionATemperatura(tensionVT);

  tensionVC = temperaturaATension(temperaturaVC);

  if (tensionVC < 0) tensionVC = 0;
  if (tensionVC > Vref) tensionVC = Vref;

  valorDAC = (tensionVC / Vref) * 4095;

  delta = (temperaturaVC - temperaturaVT) / 175.0;
  if (delta < 0) delta = 0;

  ciclos = delta * base * mult;

  if (contador <= ciclos) {
    calentando = true;
  } else {
    calentando = false;
  }

  if (contador >= base) {
    contador = 0;
  } else {
    contador += 1;
  }

  if (calentando) {
    analogWrite(DAC_output, valorDAC);
  } else {
    analogWrite(DAC_output, 0);
  }

  mostrarDatos();

  delay(1000);
}

void leerBotones() {
  if (digitalRead(btnOK) == LOW) {
    modoAjuste = !modoAjuste;
    delay(300);
  }

  if (modoAjuste) {
    if (digitalRead(btnUp) == LOW) {
      temperaturaVC += 1.0;
      if (temperaturaVC > Tmax) temperaturaVC = Tmax;
      delay(200);
    }

    if (digitalRead(btnDown) == LOW) {
      temperaturaVC -= 1.0;
      if (temperaturaVC < 0.0) temperaturaVC = 0.0;
      delay(200);
    }
  }
}

void mostrarDatos() {
  lcd.setCursor(0, 0);
  lcd.print("TC=");
  lcd.print(temperaturaVC, 1);
  lcd.print("C ");

  if (modoAjuste) {
    lcd.print("SET");
  } else {
    lcd.print(calentando ? "ON " : "OFF");
  }

  lcd.setCursor(0, 1);
  lcd.print("TE=");
  lcd.print(temperaturaVT, 1);
  lcd.print("C       ");

  Serial.print("TC = ");
  Serial.print(temperaturaVC, 1);
  Serial.print(" C | TE = ");
  Serial.print(temperaturaVT, 1);
  Serial.print(" C | Estado = ");
  Serial.print(calentando ? "CALENTANDO" : "APAGADO");
  Serial.print(" | Modo = ");
  Serial.print(modoAjuste ? "AJUSTE" : "CONTROL");
  Serial.print(" | Contador = ");
  Serial.println(contador);
}