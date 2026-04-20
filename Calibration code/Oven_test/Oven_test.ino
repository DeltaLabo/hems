/*
  Analog input, analog output, serial output

  Reads an analog input pin, maps the result to a range from 0 to 255 and uses
  the result to set the pulse width modulation (PWM) of an output pin.
  Also prints the results to the Serial Monitor.

  The circuit:
  - potentiometer connected to analog pin 0.
    Center pin of the potentiometer goes to the analog pin.
    side pins of the potentiometer go to +5V and ground
  - LED connected from digital pin 9 to ground through 220 ohm resistor

  created 29 Dec. 2008
  modified 9 Apr 2012
  by Tom Igoe

  This example code is in the public domain.

  https://docs.arduino.cc/built-in-examples/analog/AnalogInOutSerial/
*/

// These constants won't change. They're used to give names to the pins used:
const int VC = A1;  // Pin de lectura de tensión VT
const int VT = A2;  // Pin de lectura de tensión adicional (en caso de requerirse)
const int DAC_output = A0;  // Pin de salida del DAC

//Definición de variables
int medicionVT = 0;   // variable para valor de tensión entre 0 y 1024 (capacidad máxima de puerto digital)
float tensionVT = 0;  // valor en volts correspondiente al valor digital medido
float tensionVC = 0;  // valor en volts para la tensión de control
float salidaVC = 100; 

void setup() {
  // Se inicia el comando serial:
  Serial.begin(9600);
  while (!Serial) delay(10);
  Serial.println(F("\Oven automatic control system"));

  pinMode(DAC_output, OUTPUT); //Se coloca el pin DAC como salida
  analogWriteResolution(12);  // asegura rango 0–4095

}

void loop() {

  medicionVT = analogRead(VT);        //Lee el valor digital de la señal
  tensionVT = medicionVT*5.0/1023.0;  //Se tr
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
