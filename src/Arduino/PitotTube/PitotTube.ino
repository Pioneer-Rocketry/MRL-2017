#include <SPI.h>
#include <SD.h>

#define MAX_ANALOG_VOLTAGE 5
#define MAX_ANALOG_READING 1023
#define BLINK_MAX_COUNT 1

const int chipSelect = 3;
const int analogPin = A0;
const int ledPin = 13;
bool ledOn = false;
int blinkCount = 0;
long count = 0;

File dataFile;

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);

  pinMode(ledPin, OUTPUT);  
  digitalWrite(ledPin, HIGH);

  Serial.print("Initializing SD card...");

  pinMode(chipSelect, OUTPUT);
  digitalWrite(chipSelect, HIGH);
  if (!SD.begin(chipSelect)) {
    Serial.println("Card failed, or not present");

  }
  else
  {
    Serial.println("card initialized.");

    dataFile = SD.open("datalog1.csv", FILE_WRITE);

    dataFile.print("Time (ms), Voltage (V), Raw reading\n");
  }
}

void loop() {
  // make a string for assembling the data to log:
  String dataString = "";


  int analogValue = analogRead(analogPin);

  count++;
  Serial.println(count * 20);

  if(ledOn)
    digitalWrite(ledPin, HIGH);
  else
    digitalWrite(ledPin, LOW);

  if(blinkCount >= BLINK_MAX_COUNT)
  {
    ledOn = !ledOn;
    blinkCount = 0;
  }

  blinkCount++;
  

  dataString = "1234567890123456789";

  /*dataString += millis();

  dataString += ",";

  dataString += String( MAX_ANALOG_VOLTAGE *  ((float)analogValue/MAX_ANALOG_READING) );

  dataString += ",";

  dataString += String(analogValue);

  dataString += "\n";*/

  // if the file is available, write to it:
  
  dataFile = SD.open("datalog1.csv", FILE_WRITE);
  
  if (dataFile) {
    Serial.println("Written");
    dataFile.print(dataString);
    dataFile.flush();
    dataFile.close();
  }
}
