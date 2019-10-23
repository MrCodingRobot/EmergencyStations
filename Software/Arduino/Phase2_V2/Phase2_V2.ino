/////////////////////////////////////////////////////////////////////////
// Background Information

/*

Wiring:
Arduino 5V -> RB 5VIN
Arduino GND -> RB GND
Arduino GPIO 4 -> RB ON/OFF
Arduino TX3 (GPIO 14) -> RB TX
Arduino RX3 (GPIO 15) -> RB RX
Weight Sensors -> A0-A3, 3.3V -> A4, 5V/GND to 5V/GND on weight sensors.
SD card -> MOSI = 51, SS = 53, MISO = 50, CLK = 52, GND, 5V
Temperature/Humidity sensor (DHT11)  -> (-) = GND, (+) = 5V, (S) = 49

*/

/////////////////////////////////////////////////////////////////////////
// Libraries

#include <IridiumSBD.h> // RockBLOCK library
#include <Wire.h> // RTC Module (I2C communication)
#include <RTClib.h> // RTC Module
#include <SD.h> // SD card Module (SPI communication)
#include <SPI.h> // Library for SPI communication
#include <dht.h> // Temperature and humidity sensor library 

/////////////////////////////////////////////////////////////////////////
// Constants

//Station Identifiers
const uint8_t STATION_NUMBER = 6;
const char ROCKBLOCK_NUMBER[] = "300234067929930";

// Pin Setup
const int WEIGHT_SENSORS_PINS[] = {A0,A1,A2}; // Weight Sensors
const int BATTERY_MONITOR = 58;
const int PANEL_CURRENT = 59; 
const int CS_PIN = 53;
const int SD_POW_PIN = 8;
const int DHT11_PIN = 49;

// Calibration Curve (FC2231)
const float ADC2LBS_SLOPE = 0.12541; // eventually this value is calculated during calibration routine

// Constants for ACS723 current Sensor
const float I_SNSR_ADC_TO_A_SLOPE = 12.299; // slope for ADC to amps calibration curve for ACS723 current sensor
const float I_SNSR_ADC_TO_A_INTCPT = -6290; // y-intercept for ADC to amps calibration curve for ACS723 current sensor

// Constants for resistive voltage Sensor
const float V_SNSR_ADC_TO_V_SLOPE = 0.0131; // slope for ADC to volts calibration curve for resistive battery monitor
const float V_SNSR_ADC_TO_V_INTCPT = 0.047; // y-intercept for ADC to volts calibration curve

// Alarm Parameters
const float LOW_WEIGHT_TRIGGER = 25.02; // in lbs, (3 jugs)
const float LOW_VOLTAGE_TRIGGER = 12.45;
const float HIGH_VOLTAGE_TRIGGER = 15.2;
const float HIGH_CURRENT_TRIGGER = 4000;

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

// Alarm Array (for considering multiple alarm conditions
uint8_t alarms[] = {0,0,0}; // Weight, Voltage, and Current alarms
uint8_t alarm_total_value = 0;

// RockBLOCK global object
IridiumSBD modem(IridiumSerial, SLEEP_PIN);

// RTC global object
RTC_PCF8523 rtc;

// Temp & Humidity global object
dht dht_sensor;

// Normalize Sensor Reference Values
uint32_t zero_weight_sensor_values[] = {0,0,0};
uint32_t slope_weight_sensor_values[] = {0,0,0};
uint32_t barrel_weight_sensor_values[] = {0,0,0};

uint32_t barrel_weight_sensor_value = 0;
uint32_t slope_weight_sensor_value = 0;

double placed_test_weight = 0;
double adc2lbs_slope = 0;
float barrel_weight = 0;

// SD Card CSV File variables
String csv_filename = "";

void setup() {
  
  // Serial Port Setup
  Serial.begin(115200);
  while (!Serial); // waiting for serial port to start up

  // RockBLOCK Setup
  IridiumSerial.begin(19200);
  
  // RTC Setup
  Wire.begin();
  rtc.begin();
  
  if (!rtc.begin()){
    Serial.println("Couldn't find RTC");
	while(1);
  }
  
  if (!rtc.initialized()) Serial.println("RTC is NOT running");
  
  // SD card Setup
  if (!SD.begin(CS_PIN)) Serial.println("SD Card Problem: Failure to being connection");

  csv_filename = "Station_" + String(STATION_NUMBER) + "__" + time_now.timestamp();
  File data_file = SD.open(csv_filename, FILE_WRITE);
  if (data_file){
    data_file.println(F("New Log Started"));
	data_file.println(F("Date, Time, Battery Voltage (V), Panel Current (A), \
	                    Weight (lbs), Temperature (C), Temperature (F), \
						Humidity (%), Active"));
  }
  else Serial.println(F("Couldn't open log file on SD Card"));

  // Transmitted Data Array Setup
  data[0] = STATION_NUMBER;
  data[1] = ALL_GOOD;
  for (int i = 2; i < DATA_ARRAY_SIZE; i++){
    data[i] = 0;
  }
  
  // Calibration Routine (Zero Weight and Barrel Weight)
  calibrationRoutine();
  
  // First fast collection of data
  completeDataCollection(20, "seconds"); // Delay of 20 seconds between measurement

  /* 
  Previous pseudocode
  
  // Read weight values (they failed to do this but wanted to)

  // Read battery voltage and panel current

  // Initialize RTC

  // Initalize SD Card

  // Debugging and Light up of troubleshoot light
  
  */
}

void loop() {


  rockBlockSetup();
  dataTransmission();
  rockBlockSleep();
  
  
  completeDataCollection(20, "seconds"); // Delay of 20 seconds between measurement

  /* 
  Previous pseudocode
  
  // read voltage, current, and weight sensors

  // check time with RTC

  // if sat_save_flag is True, save data array and check alarms

  // after if statement, check alarms again?

  // then save lastest values to 45,46,47 index of data_array

  // send data with rockBlock

  // if sd_svae flag is True, save data to SD card

  // check or reset alarms again?
  
  */

  

}
