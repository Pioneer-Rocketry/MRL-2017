/********************************************************************
 *                        PIONEER ROCKETRY                          *
 *    The following code has been adapted from another project      *
 *                                                                  *
 ********************************************************************/
// Test code for Adafruit GPS modules using MTK3329/MTK3339 driver
//
// This code shows how to listen to the GPS module in an interrupt
// which allows the program to have more 'freedom' - just parse
// when a new NMEA sentence is available! Then access data when
// desired.
//
// Tested and works great with the Adafruit Ultimate GPS module
// using MTK33x9 chipset
//    ------> http://www.adafruit.com/products/746
// Pick one up today at the Adafruit electronics shop 
// and help support open source hardware & software! -ada

//This code is intended for use with Arduino Leonardo and other ATmega32U4-based Arduinos

#include "Adafruit_GPS.h"
#include <SoftwareSerial.h>
#include "XBEE.h"


#include <SPI.h>
#include <SD.h>

const int chipSelect = 10;
File myFile;

// Connect the GPS Power pin to 5V
// Connect the GPS Ground pin to ground
// If using software serial (sketch example default):
//   Connect the GPS TX (transmit) pin to Digital 8
//   Connect the GPS RX (receive) pin to Digital 7
// If using hardware serial:
//   Connect the GPS TX (transmit) pin to Arduino RX1 (Digital 0)
//   Connect the GPS RX (receive) pin to matching TX1 (Digital 1)

// If using software serial, keep these lines enabled
// (you can change the pin numbers to match your wiring):
SoftwareSerial mySerial(8, 7);
Adafruit_GPS GPS(&mySerial);

XBEE * x1;

// If using hardware serial, comment
// out the above two lines and enable these two lines instead:
//Adafruit_GPS GPS(&Serial1);
//HardwareSerial mySerial = Serial1;

// Set GPSECHO to 'false' to turn off echoing the GPS data to the Serial console
// Set to 'true' if you want to debug and listen to the raw GPS sentences
#define GPSECHO  true

void setup() {

    x1 = new XBEE();

    x1->Initialize(57600, 2);
    Serial.begin(9600);

    pinMode(10, OUTPUT);
    digitalWrite(10, HIGH);
    if (!SD.begin(10)) {
        //Well shit...
        x1->println("SD NOT INITIALIZED :(");

    }
    else
    {
      x1->println("SD INITIALIZED!");
    }

    myFile = SD.open("data.csv", FILE_WRITE);    
 
    if(myFile)
    {

      myFile.print("Time, Date, Fix, Quality, Latitude, Longitude, Speed, Angle, Altitude, Satellites\n");
      myFile.flush();
      
    }
  

    // connect at 115200 so we can read the GPS fast enough and echo without dropping chars
    // also spit it out
    //Serial.begin(115200);
    //delay(5000);
    //Serial.println("Adafruit GPS library basic test!");

    // 9600 NMEA is the default baud rate for Adafruit MTK GPS's- some use 4800
    GPS.begin(9600);

    // uncomment this line to turn on RMC (recommended minimum) and GGA (fix data) including altitude
    GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
    // uncomment this line to turn on only the "minimum recommended" data
    //GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
    // For parsing data, we don't suggest using anything but either RMC only or RMC+GGA since
    // the parser doesn't care about other sentences at this time

    // Set the update rate
    GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);   // 1 Hz update rate
    // For the parsing code to work nicely and have time to sort thru the data, and
    // print it out we don't suggest using anything higher than 1 Hz

    // Request updates on antenna status, comment out to keep quiet
    GPS.sendCommand(PGCMD_ANTENNA);


    delay(1000);
    // Ask for firmware version
    x1->println(PMTK_Q_RELEASE);

    x1->println("READY!");    
}

uint32_t timer = millis();

char* nemaPointer;

String dataString;

void loop()
{
    char c = GPS.read();
    
    dataString = "";
    
    // if a sentence is received, we can check the checksum, parse it...
    if (GPS.newNMEAreceived()) {
        
        //Print to the file first.
        dataString += String((int)GPS.hour, DEC);
        dataString += ":";
        dataString += String((int)GPS.minute, DEC);
        dataString += ":";
        dataString += String((int)GPS.seconds, DEC);
        dataString += ".";
        dataString += String(GPS.milliseconds);

        dataString += ",";

        dataString += String(GPS.day, DEC);
        dataString += "/";
        dataString += String(GPS.month, DEC);
        dataString += "/20";
        dataString += String(GPS.year, DEC);

        dataString += ",";
        dataString += String((int) GPS.fix);

        dataString += ",";

        dataString += String((int) GPS.fixquality);

        if (GPS.fix || GPS.fixquality != 0) {

        
            dataString += ",";

            dataString += String(GPS.latitude_fixed);

            dataString += ",";
  
            dataString += String(GPS.longitude_fixed);

            dataString += ",";

            dataString += String(GPS.speed);

            dataString += ",";

            dataString += String(GPS.angle);

            dataString += ",";

            dataString += String(GPS.altitude);

            dataString += ",";

            dataString += String((int)GPS.satellites);
            
        }

        x1->println(dataString.c_str());

        dataString += "\n";
        
        myFile.print(dataString);
       
        myFile.flush();
        
        GPS.flagNMEAreceived(); // Juat mark it recieved so we can start recieving again.

    }

}
