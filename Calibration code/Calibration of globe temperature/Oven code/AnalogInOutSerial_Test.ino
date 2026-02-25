/*
  Analog input, analog output, serial output

  Reads an analog input pin, maps the result to a range from 0 to 255 and uses
  the result to set the pulse width modulation (PWM) of an output pin.
  Also prints the results to the Serial Monitor.

  The example code is in the public domain. The code below was modified for the final purposes.

  https://docs.arduino.cc/built-in-examples/analog/AnalogInOutSerial/
*/

// These constants won't change. They're used to give names to the pins used:
const int VC = A1;  // Pin de lectura de tensión VT
const int VT = A2;  // Pin de lectura de tensión adicional (en caso de requerirse)
const int DAC_output = A0;  // Pin de salida del DAC

//Definición de variables
int medicionVT = 0;
float tensionVT = 0;
float tensionVC = 0;
float salidaVC = 100;
char tecla;

void setup() {
  // Se inicia el comando serial:
  Serial.begin(9600);
  pinMode(DAC_output, OUTPUT); //Se coloca el pin DAC como salida
  analogWriteResolution(12);  // asegura rango 0–4095
}

void loop() {

  if (Serial.available() > 0) {
    char tecla = Serial.read();
  }

  if (tecla == 'a'){

    medicionVT = analogRead(VT);
    tensionVT = medicionVT*5.0/1023.0;
    tensionVC = 0.6;

    Serial.print("Tension VC de control= ");
    Serial.println(tensionVC);
    Serial.print("Tensión VT inicial= ");
    Serial.println(tensionVT);

    // Mantener tensionVC en el DAC hasta que tensionVT >= 70% de tensionVC
    while (tensionVT < tensionVC * 0.7) {
        analogWrite(DAC_output, tensionVC);

        // Se actualiza la tensionVT en cada iteración
        medicionVT = analogRead(VT);  
        tensionVT = medicionVT*5.0/1023.0;

          // print the results to the Serial Monitor:
        Serial.print("Tensión VT = ");
        Serial.print(tensionVT);
        Serial.print(" Porcentaje de VT respecto a VC");
        Serial.println(tensionVT/tensionVC*100);

         delay(100);
    }

    // Cuando salga del while, poner el DAC en 0
    analogWrite(DAC_output, 0);

  }

  // read the analog in value:
  // medicionVC = analogRead(VC);
  

  //if (tensionVT < tensionVC*0.7) {
  //  analogWrite(DAC_output, tensionVC);
  //}

  //else{
  //  analogWrite(DAC_output, 0);
  //}

  // map it to the range of the analog out:
  // tensionVC = medicionVC*5.0/1023.0;

  //outputValue = map(sensorValue, 0, 255, 0.0, 5.0);
  // change the analog out value:
  //analogWrite(analogOutPin, outputValue);

  // wait 2 milliseconds before the next loop for the analog-to-digital
  // converter to settle after the last reading:
 
}
