////////////////////////////////////////////////////////////////////////
// Background Information

/*
Author: Eduardo Davalos
Last Updated: 7/30/2019

Purpose: Sample weight sensors, perform calculations, and transmitt the
weight information with the rockBlock. 

Wiring:
Arduino 5V -> RB 5VIN
Arduino GND -> RB GND
Arduino GPIO 4 -> RB ON/OFF
Arduino TX3 (GPIO 14) -> RB TX
Arduino RX3 (GPIO 15) -> RB RX
Weight Sensors -> A0-A3
3.3V Reference -> A8
5V/GND to 5V/GND on weight sensors.

To Do:
Test the entire station together

Additional useful information:
 - Jugs standard (1 Gallon) have standard weight of 8.34 lbs
 - Acceptable error value: < 4 lbs (49 % of a jug)
*/

////////////////////////////////////////////////////////////////////////
// Libraries

#include <IridiumSBD.h> // RockBLOCK library

////////////////////////////////////////////////////////////////////////
// Constants

// Station Identifiers
const uint8_t STATION_NUMBER = 3;
const char ROCKBLOCK_NUMBER[] = "300234067431270";

// Pin Setup
const int WEIGHT_SENSORS_PINS[] = {A0,A1,A2,A8}; // 3 sensors and reference

// Calibration Curve (FC2231)
const float ADC2LBS_SLOPE = 0.12541; // eventually this value is calculated during calibration routine
//const float ADC2LBS_INTERCEPT = 0; // y-intercept for ADC to lbs calibration curve

// Alarm Parameters
const float LOW_WEIGHT_TRIGGER = 25.02; // in lbs, (3 jugs)

// Transmitted Data 
const size_t DATA_ARRAY_SIZE = 48;

// Sampling Parameter
const int NUMBER_OF_SAMPLES = 800;

// RockBLOCK Constants
#define IridiumSerial Serial3 // Rx15 and Tx 14 -> NOTE: If you aren't using a MEGA you will probably have to change this.
const int SLEEP_PIN = 4;
const int NUMBER_OF_TRANSMISSION_ATTEMPTS = 20;

// Alarm Constants

// Phase One and Two Alarms
#define ALL_GOOD 0;
#define LOW_WEIGHT 1;
#define BARREL_REMOVED 2;
#define HIGH_WEIGHT 3;

// Phase Two Only Alarms
#define HIGH_CURRENT 4;
#define LOW_VOLTAGE 5;
#define HIGH_VOLTAGE 6;
#define CHECK_STATION 7;

////////////////////////////////////////////////////////////////////////
// Global Variables

// Transmitted Data
uint8_t data[DATA_ARRAY_SIZE];
uint8_t *data_pointer = &data[0];

// RockBLOCK global object
IridiumSBD modem(IridiumSerial, SLEEP_PIN);

// Normalize Sensor Reference Values
//uint32_t zero_weight_sensor_values[] = {0,0,0};
//uint32_t slope_weight_sensor_values[] = {0,0,0};
//uint32_t barrel_weight_sensor_values[] = {0,0,0};

uint32_t zero_weight_sensor_values[] = {107,117,99};
uint32_t slope_weight_sensor_values[] = {0,0,0};
uint32_t barrel_weight_sensor_values[] = {177,177,129};

//uint32_t barrel_weight_sensor_value = 0;
uint32_t barrel_weight_sensor_value = 22.70;
uint32_t slope_weight_sensor_value = 0;

double placed_test_weight = 0;
//double adc2lbs_slope = 0;
double adc2lbs_slope = 0.13031;
//double adc2lbs_slope = 0.30031;
float barrel_weight = 0;

////////////////////////////////////////////////////////////////////////
// Main Code

void setup() {

  // Serial Port Setup
  Serial.begin(115200);
  while (!Serial); // waiting for serial port to start up

  // RockBLOCK Setup
  IridiumSerial.begin(19200);

  // Transmitted Data Array Setup
  data[0] = STATION_NUMBER;
  data[1] = ALL_GOOD; 
  for (int i = 2; i < 47; i++){
    data[i] = 0;
  }

  // Calibration Routine (Zero Weight and Barrel Weight)
  //calibrationRoutine();

  // First fast collection of data
  completeDataCollection(10, "seconds"); // Delay of 20 seconds between measurement

}

void loop() {

  // Troubleshooting weight sensors
  //printRawData();
  //delay(200);
  
  rockBlockSetup();
  dataTransmission();
  rockBlockSleep();
  
  
  completeDataCollection(90, "minutes"); // Delay of 20 seconds between measurement
}
