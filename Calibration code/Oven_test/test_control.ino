#include <LiquidCrystal.h>

const int VT = A2;
const int DAC_output = A0;

const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;

const int btnUp = 6;
const int btnDown = 7;
const int btnOK = 8;

float tensionVT = 0;
float tensionVC = 0.6;
float Vref = 5.0;
int valorDAC = 0;

bool calentando = true;
bool modoAjuste = false;

LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

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

  valorDAC = (tensionVC / Vref) * 4095;

  if (calentando && tensionVT >= tensionVC * 0.70) {
    calentando = false;
  }

  if (!calentando && tensionVT <= tensionVC * 0.50) {
    calentando = true;
  }

  if (calentando) {
    analogWrite(DAC_output, valorDAC);
  } else {
    analogWrite(DAC_output, 0);
  }

  mostrarDatos();

  delay(200);
}

void leerBotones() {
  if (digitalRead(btnOK) == LOW) {
    modoAjuste = !modoAjuste;
    delay(300);
  }

  if (modoAjuste) {
    if (digitalRead(btnUp) == LOW) {
      tensionVC += 0.05;
      if (tensionVC > 5.0) tensionVC = 5.0;
      delay(200);
    }

    if (digitalRead(btnDown) == LOW) {
      tensionVC -= 0.05;
      if (tensionVC < 0.0) tensionVC = 0.0;
      delay(200);
    }
  }
}

void mostrarDatos() {
  lcd.setCursor(0, 0);
  lcd.print("VC=");
  lcd.print(tensionVC, 2);
  lcd.print("V ");

  if (modoAjuste) {
    lcd.print("SET");
  } else {
    lcd.print(calentando ? "ON " : "OFF");
  }

  lcd.setCursor(0, 1);
  lcd.print("VT=");
  lcd.print(tensionVT, 2);
  lcd.print("V       ");

  Serial.print("VC = ");
  Serial.print(tensionVC, 2);
  Serial.print(" V | VT = ");
  Serial.print(tensionVT, 2);
  Serial.print(" V | Estado = ");
  Serial.print(calentando ? "CALENTANDO" : "APAGADO");
  Serial.print(" | Modo = ");
  Serial.println(modoAjuste ? "AJUSTE" : "CONTROL");
}