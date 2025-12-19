#include <Arduino.h>
#include <SparkFun_AS7331.h>
#include <Wire.h>

SfeAS7331ArdI2C myUV;

void setup()
{
    Serial.begin(115200);
    while (!Serial)
    {
        delay(100);
    };

    Wire.begin();

    // Initialize sensor and run default setup.
    if (myUV.begin() == false)
    {
        Serial.println("Sensor failed to begin. Please check your wiring!");
        Serial.println("Halting...");
        while (1);
    }

    Serial.println("Sensor began.");

    // Set measurement mode and change device operating mode to measure.
    if (myUV.prepareMeasurement(MEAS_MODE_CMD) == false)
    {
        Serial.println("Sensor did not get set properly.");
        Serial.println("Halting...");
        while (1);
    }

    Serial.println("Set mode to command.");
    
    // Encabezado del csv
    Serial.println("UVA,UVB,UVC");
}

void loop()
{

    // Send a start measurement command.
    if (ksfTkErrOk != myUV.setStartState(true))
        Serial.println("Error starting reading!");

    // Wait for a bit longer than the conversion time.
    delay(2 + myUV.getConversionTimeMillis());

    // Read UV values.
    if (ksfTkErrOk != myUV.readAllUV())
        Serial.println("Error reading UV.");

    Serial.print(myUV.getUVA());
    Serial.print(",");
    Serial.print(myUV.getUVB());
    Serial.print(",");
    Serial.println(myUV.getUVC());

    delay(2000);
}
