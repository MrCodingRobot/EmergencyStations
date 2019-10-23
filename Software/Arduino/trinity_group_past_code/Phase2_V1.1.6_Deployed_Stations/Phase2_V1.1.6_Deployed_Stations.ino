//Phase 2 V1.1.3 Deloyed Stations Code for Trinity University Water Stations Project
//Authors: Sean Farrell, Caroline Kutach, Nathan Richter, Brady Burns, Brian Guenther, and Zach
//Last Update:
//--5/30/19
/* Updates to the satellite transmission array 
   * Underflow and overflow checking and handling
   * Set up unique alarms for low weight, high weight and barrel removed
*/
//--5/15/19: 
/* This version ws transitioned from V1.1.4 to V1.1.5. In this version the Satellite modem tries to send continuously in main loop
   * Also reduced the alarms to only trigger based on the weight sensor readings. I also changed it to send data twice a day at 7:00 am (7) 
   * and 6:00 pm (18). This was changed from just sending at 6:00am because we found that we could not transmit at this time with old tranmission algorithm.
*/     
//--3/21/19
/* Requirements:
   *Irridium SBD Library installed, Version of Arduino must be 1.6.21, Arduino MEGA, RockBLOCK V2.c, 4 Weight Sensors, 5 Temperature and Humidity Sensor
  
   *Wiring:
   *Arduino 5V -> RB 5VIN, Arduino GND -> RB GND, Arduino GPIO 4 -> RB ON/OFF, Arduino TX3 (GPIO 14) -> RB TX, Arduino RX3 (GPIO 15) -> RB RX,
   *Weight Sensors -> A0-A3, 3.3V -> A4, 5V/GND to 5V/GND on weight sensors.
   *SD card -> MOSI = 51, SS = 53, MISO = 50, CLK = 52, GND, 5V
   *Temperature/Humidity sensor (DHT11)  -> (-) = GND, (+) = 5V, (S) = 49
   *NOTE: Read to Read and write to write (This is weird)

   *Purpose:
   *This code is used to read the water weight at each of the water stations deployed by the South Texas Human
   *Rights Association and send that data via satellite to be uploaded to thier website.
   *Key objectives of the code are listed below:
   *1) Read weight using Analog ports and GPS location using Satellite module
   *2) Keep track of real time using Real Time CLock (RTC) module
   *3) Send weight data at standard intervals (currently set to 7:00am and 7:00pm)
   *4) Read station parameters (battery voltage, current)
   *5) Save station parameters to a removable SD card (acting like EEPROM)
*/
//Station Identifiers
const uint8_t STATION_NUMBER = 6;
const char    ROCKBLOCK_NUMBER[] = "300234067929930";

//Include Libraries
#include <IridiumSBD.h>                   //Satellite Module
#include <SoftwareSerial.h>               //Satellite Module
//#include "HX711.h"                        //Weight Sensors
#include <Wire.h>                         //RTC Module (I2C commuication)
#include <RTClib.h>                       //RTC Module
#include <SD.h>                           //SD card Module (SPI communication)
#include <SPI.h>                          //Library for SPI communication
#include <dht.h>                          //Temperature and humidity sensor library

//*********************************************************************************************************************************************************//
/*
   Section of code is designated for Defintions, Constants, and Variable Declarations
   It is ordered 1) Rockblock (Satellite module), 2) Sensors, 3) Real Time Clock (RTC), 4) SD Card Module
*/
// --------ROCKBLOCK SECTION:
// Definitions used for controlling RockBLOCK
#define IridiumSerial Serial3       // Rx15 and Tx 14 -> NOTE: If you aren't using a MEGA you will probably have to change this.
#define DIAGNOSTICS false           // Change this to see diagnostics
const int SLEEP_PIN = 4;            // This pin is used to turn satellite module on/off

// Initializing Debugging Variables
int signalQuality = -1;             // Used for testing signal strength
int err;                            // Used for status of built in functions of library
int initialized = 1;                // Used during boot to send water station location and water amount to website

//Initializing/Clearing Array that holds analog values
const size_t data_array_size = 48;
uint8_t data[data_array_size];
int sample_pos = 0;                 //location within the character array

// Declare the IridiumSBD object (Initializing Satellite communication with on/off pin and serial pins)
IridiumSBD modem(IridiumSerial, SLEEP_PIN);

//variables used for improved satellite transmission method
int long current_time = 0;          //gives back current time in seconds from 1/1/1970
int long send_time = 0;             //holds the last time it tried to end data 
boolean sat_signalerr_flag = false; //set when signal quality is < 3 during transmission
int sat_send_attempt = 0;           //records how many times the function has tried sending satellite data

//--------SENSORS SECTION:
const int BATTERY_MONITOR = 58;     //battery voltage monitor (analog) A4
const int PANEL_CURRENT = 59;       //solar panel current monitor (analog) A5
float WEIGHT_SENSOR1 = A1;          // Analog weight sensors
float WEIGHT_SENSOR2 = A2;
float WEIGHT_SENSOR3 = A3;
//#define HX711_DT  22                //HX711 load cell amplifier
//#define HX711_CLK  23

//Constants for HX711 weight amplfier or FC2231 load cells
//const int communication_period = 1800;          //Period at which communications triggers
const int scale_calibration_factor = -9437;       //This value is obtained using the SparkFun_HX711_Calibration sketch
const float FC2231_ADC_TO_LBS_SLOPE = 0.37;       //slope for ADC to lbs calibration curve
const float FC2231_ADC_TO_LBS_INTCPT = -41.5;     //y-intercept for ADC to lbs calibration curve

const float WGHT_DIFF_TRIG = 0.2;                 //weight difference to trigger weight update

//Constants for ACS723 current Sensor
const float I_SNSR_ADC_TO_A_SLOPE = 12.299;       //slope for ADC to amps calibration curve for ACS723 current sensor
const float I_SNSR_ADC_TO_A_INTCPT = -6290;       //y-intercept for ADC to amps calibration curve for ACS723 current sensor

//Constants for resistive voltage Sensor
const float V_SNSR_ADC_TO_V_SLOPE = 0.0131;       //slope for ADC to volts calibration curve for resistive battery monitor
const float V_SNSR_ADC_TO_V_INTCPT = 0.047;       //y-intercept for ADC to volts calibration curve

//--Alarms, values control when alarms are triggered and when they are reset
const float LOW_WGHT_TRIG = 25;                   //low weight trigger (in lbs), 60 = ~7 jugs of water (1 jug = 8.34 lbs)
const float LOW_WGHT_RST = 110;                   //reset for the low weight alarm (in lbs)
const float HIGH_WGHT_TRIG = 350;                 //high weight trigger (in lbs)
const float HIGH_WGHT_RST = 300;                  //reset for the high weight alarm
const float HIGH_I_TRIG = 4000;                   //high current at which alarm is activated. (in A)
const float HIGH_I_RST = 3200;                    //reset for the high current alarm (in A)
const float LOW_V_TRIG = 12.45;                   //battery voltage to set low votlage alarm (in V)
const float LOW_V_RST = 12.71;                    //voltage required to reset the low voltage alarm (in V)
const float HIGH_V_TRIG = 15.2;                   //high battery voltage trigger (in V)
const float HIGH_V_RST = 14.7;                    //reset for the low voltage alarm (in V)
const float BARREL_WGHT = 36.4;                   //weight of the water barrel and the shelving unit

//Alarms -flags
boolean alarms_triggered = false;                 //this is set by the alarm triggers (voltage, weight, current)
const int ALARMTIMES[] = {7, 7, 19, 19};          //array hold the times alarms will transmit data if alarms are set (in military time)

float weight = 0.0;                               //actual net weight (recorded weight, in lbs)
float scale_weight = 0.0;                         //weight as read from scale (current weight, in lbs)
float battery_voltage = 0.0;                      //(in V) 
float panel_current = 0.0;                        //(in mA)

//HX711 scale(HX711_DT, HX711_CLK);

// -------REAL TIME CLOCK (RTC) SECTION:
//Set RTC PINS, on standard I2C pins for Arduino Mega, (from wire library) I2C pins: 20 (SDA), 21(SCL)
const int morn_time = 7;                          //(military time) sets to send data at 7:00 am
const int night_time = 19;                        //(military time) sets to send data at 6:00 pm
const int sat_data_save_period = 50;//51;              // value between 1-60 (in minutes) ()
//const int sat_data_save_period =12;               // value between 1-60 (in minutes) (FOR DEBUGGING)
const int SD_save_period = 1;                     // value between 1-60 (in minutes)
boolean SD_save_flag = false;                     // flags to tell main to perform operations
boolean sat_save_flag = false;
boolean sat_send_flag = false;
int sat_old_minute = 0;                            //previous minute data was saved for sat, on boot up save minutes for satellite timing comparison
int SD_old_minute = 0;                             //previous minute data was saved on SD, on boot up save minutes for SD saving comparison
int sat_sent_hr = 0;                               //previous hour that data was transmitted
int SD_save_min = 0;                               //saves the minutes that data was logged on the SD card MAY BE REDUNDANT WITH SD_old_minute
int sat_save_min = 0;                              //saves the minutes sat data was added to character array MAY BE REDUNDANT WITH sat_old_minute

//Define an RTC object
RTC_PCF8523 rtc;

//Date and Time String Initilization
int days, hours, minutes, seconds;
int timeInt[3], dateInt[3], timeCheck[3], dateCheck[3];

// -------- SD CARD SECTION:
const int  CS_PIN = 53;                        // SD card uses standard SPI pins (check if not Arduino Mega)
const int SD_POW_PIN = 8;

//Initialize time strings used to save time stamp to SD card
String SD_year, SD_month, SD_day, SD_hour, SD_minute, SD_second, SD_time, SD_date;

// ------ TEMPERATURE AND HUMIDITY SENSOR SECTION:
#define DHT11_PIN 49
dht DHT;
float tempFahrenheit = 0.0;
float tempCelcsius = 0.0;
float humidity = 0.0;

// ------ Non-invasive Debugging Tools
const int GREEN_PIN = 39;
const int YELLOW_PIN = 37;
const int RED_PIN = 35;
const int SAT_SEND_PIN = 33;
bool debugging_flag;
//*********************************************************************************************************************************************************//
/*
   Section of code is designated for functions other than setup and loop
   It is ordered 1) checkTime, 2) SD_save, 3) sendingData, 4) debugging functions
*/
//*********************************************************************************************************************************************************//
// This function is responsible for checking the Real Time Clock and saving/sending the data
/*
   First the function grabs the current real time and saves the data into the variable "datatime". It then decomposes the
   information into more descrete forms of time such as years, months, days...minutes,seconds.
   It then checks if the current time is equal to the set "morn_time", "night_time", "initalize", or
   parameter triggers. If any of these are true then it sends data using the satellite module.
   It also checks the SD card saving period "SD_period" to see if it should save the data to the SD card

   Note: that "SD_force_save" is used to save data to the SD card everytime data is sent to the satellite module
*/
void checkTime(int* sat_old_minute, int* SD_old_minute, bool* sat_send_flag, bool* sat_save_flag, bool* SD_save_flag,
               int* sat_sent_hr, int* sat_save_min, int* SD_save_min, bool alarms_triggered, bool initialize) {
  //Get the current date and time info and store in strings
  DateTime datetime = rtc.now();
  //Don't use int years  = (datetime.year(),  DEC); use as below
  int years  = datetime.year();
  int months = datetime.month();
  int days  = datetime.day();
  int hours  = datetime.hour();
  int minutes = datetime.minute();
  int seconds = datetime.second();

  if (initialize == 1) {
    //Concatenate the strings into date and time for when station boots up (Int = initial)
    dateInt[0] = months;
    dateInt[1] = days;
    dateInt[2] = years;
    timeInt[0] = hours;
    timeInt[1] = minutes;
    timeInt[2] = seconds;
    *sat_old_minute = minutes;                   //on boot up save minutes for satellite timing comparison
    *sat_save_min = minutes;
    *SD_old_minute = minutes;                   //on boot up save minutes for SD saving comparison
    *SD_save_min = minutes;
    *sat_sent_hr = hours;
  } else {
    //Concatenate the strings into date and time for checking when to send data next
    //dateCheck = {month, day , year};
    //timeCheck = {hour, minute, second};
    dateCheck[0] = months;
    dateCheck[1] = days;
    dateCheck[2] = years;
    timeCheck[0] = hours;
    timeCheck[1] = minutes;
    timeCheck[2] = seconds;
  }
  int dayDiff = (dateCheck[1]) - (dateInt[1]);     // Check time difference (in days)
  int hourDiff = (timeCheck[0]) - (timeInt[0]);     // Checks time difference (in hours)
  int satDiff = minutes - *sat_old_minute;          // Checks time difference (in minutes) for data saving to data array
  int SDDiff = minutes - *SD_old_minute;

  //Satellite module send data timing check based on "morn_time" and "night_time"
  // Field if statment => if ((initalize == 1)|| (abs(dayDiff)  > 0 && (timeCheck[0] == morn_time || timeCheck[0] == night_time))){      // Parameter check to see if data should be sent over satellite
  /*
     This "if" statement below is the sending conditions necessary to send data to from the satellite module
     There are three main triggers: 1) sends if program is initialized->boot up
     2) days have been larger than zero, and hour is set to morning or night hour trigger
     3) alarm has been triggered then will send at hours specified by array ALARMTIMES
     sat_sent_hr,sat_save_min,SD_save_min => keeps stuff from saving mutiple times in an hour or minute
  */
  bool satsendreleased = 0;//digitalRead(SAT_SEND_PIN);   //hold button down to force send used FOR DEBUGGING
  //  Serial.println("In the checktime function");
  //  Serial.println((String)"hours: "+hours);
  //  Serial.println((String)"timeCheck[0]: "+timeCheck[0]);
  //  Serial.println((String)"Alarm times (array): "+ALARMTIMES[0]+","+ALARMTIMES[1]+","+ALARMTIMES[2]+","+ALARMTIMES[3]);
  //  delay(5000);
  if (initialize == 1 || satsendreleased == 1 || ((timeCheck[0] - *sat_sent_hr) != 0) && ((abs(dayDiff)  >= 0 && (timeCheck[0] == morn_time || timeCheck[0] == night_time) && (!alarms_triggered))
      || (alarms_triggered && (timeCheck[0] == ALARMTIMES[0] || timeCheck[0] == ALARMTIMES[1] || timeCheck[0] == ALARMTIMES[2] ||
                               timeCheck[0] == ALARMTIMES[3])))) {
    Serial.println("Setting the sat_send_flag_true");
    *sat_send_flag = true;
    *sat_sent_hr = hours;
    //SD_force_save = 1;                         // Will force the SD card to save data after satallite module sends data
    //sendingData();                               // Send information over Satellite
  }

  //Statement below controls when data will be saved in data array for satellite module
  if ((satDiff >= sat_data_save_period || (satDiff < 0 && satDiff >= (sat_data_save_period - 60))) &&
      ((minutes - *sat_save_min) != 0)) {
    Serial.println("In the checktime function, setting sat_save_flag true");
    *sat_save_flag = true;
    *sat_old_minute = minutes;                        //when booting up save minute value
    *sat_save_min = minutes;
  }

  //Statement below controls when data will be saved on SD card
  if ((SDDiff >= SD_save_period || (SDDiff < 0 && SDDiff >= (SD_save_period - 60))) && ((minutes - *SD_save_min) != 0)) {
    Serial.println("In the checktime function, setting SD_save_flag true");
    *SD_save_flag = true;
    *SD_old_minute = minutes;
    *SD_save_min = minutes;
  }
}

//*********************************************************************************************************************************************************//
// This function is responsible for saving data to the SD card.
/*
   The inputs to this function are the measured Battery voltage, panel current, temperature, humidity
   saves the current time in SD_year, SD_month, SD_day, SD_hour, SD_minute, SD_second, SD_time, date;
   Need to add floats or ints for the temperature and then the humidty readings!
*/
void SD_save(float battery_voltage, float panel_current, float weight) {
  //Get the current date and time info and store in strings
  DateTime datetime = rtc.now();
  SD_year  = String(datetime.year(),  DEC);
  SD_month = String(datetime.month(), DEC);
  SD_day  = String(datetime.day(),  DEC);
  SD_hour  = String(datetime.hour(),  DEC);
  SD_minute = String(datetime.minute(), DEC);
  SD_second = String(datetime.second(), DEC);

  //Concatenate the strings into date and time
  SD_date = SD_year + "/" + SD_month + "/" + SD_day;
  SD_time = SD_hour + ":" + SD_minute + ":" + SD_second;

  //Read temperature and humidity using (DHT11 sensor)
  //Serial.println("Checking temperature and humidity now");
  int chk = DHT.read11(DHT11_PIN);
  //Serial.println((String)"Check "+chk);
  tempCelcsius = DHT.temperature;
  tempFahrenheit = (tempCelcsius*(1.8))+32;
  humidity = DHT.humidity;
  
  //Open a file and write to it.
  File dataFile = SD.open("WS6_FT2.csv", FILE_WRITE);
  if(dataFile) {
    //Writing the data to the SD card
    dataFile.print(SD_date);
    dataFile.print(F(","));
    dataFile.print(SD_time);
    dataFile.print(F(","));
    dataFile.print(battery_voltage);    //Battery Voltage (V)
    dataFile.print(F(","));
    dataFile.print(panel_current);      //Panel Current (A)
    dataFile.print(F(","));
    dataFile.print(weight);             //weight (lbs)
    dataFile.print(F(","));
    dataFile.print(tempCelcsius);     //Temperature (C)
    dataFile.print(F(","));
    dataFile.print(tempFahrenheit);     //Temperature (F)
    dataFile.print(F(","));
    dataFile.print(humidity);     //Humidity(%)
    dataFile.print(F(","));
    dataFile.println("Active");     //Active -- for reference data is being saved correctly
    dataFile.close(); //Data isn't actually written until we close the connection!

    //Print same thing to the screen for debugging
    Serial.print(SD_date);
    Serial.print(F(","));
    Serial.print(SD_time);
    Serial.print(F(","));
    Serial.print(battery_voltage);     //Battery Voltage (V)
    Serial.print(F(","));
    Serial.print(panel_current);     //Panel Current (A)
    Serial.print(F(","));
    Serial.print(weight);             //weight (lbs)
    Serial.print(F(","));
    Serial.print(tempCelcsius);             //Temperature (C)
    Serial.print(F(","));
    Serial.print(tempFahrenheit);             //Temperature (F)
    Serial.print(F(","));
    Serial.print(humidity);     //Humidity(%)
    Serial.print(F(","));
    Serial.println("Active");     //Active -- for reference data is being saved correctly
  } else {
    Serial.println(F("Couldn't open log file"));
  }
  //delay(refresh_rate);
}

//*************************************************************************************************************************************************************//
// This function is responsible for sending the data using the RockBLOCK module.
/* INPUTS
 * Data Array: Must be int array of 42 length
 */
/* OUTPUTS
 * Error: Integer representing the err outputted from the modem.sendSBDText function. This indicator allows us to keep trying to send data if it fails the first time.
 */
/* OPERATION
 * This function has a few key components: Initialization, Signal Quality, and Sending Data, these are separated by -------
 * Initialization: "Wakes up the Modem", prints various errors/debugging to Serial
 * Signal Quality: Tests the signal quality which can differ based on the position of the satellites or heavy cloud cover/fog. Alost prints debugging info.
 * Sending Data: First converts the int array into a char array, which allows us to send more information as the sendSBDText function is limited to 50 bytes.  
 * The reason this allows more information is if we sent "235" as characters then that would cost three ASCII bytes. 
 * However we could transfer 235 into one ASCII symbol which then only costs 1 byte.
 * Next, we create a pointer to the beginning of our char array (This is the required input to the sendSBDText function).
 * Then we Call the function, and have some options for debugging info.
 * For more info on the SBDsendText function see the Readme which has some helpful documents.
 */
int sendingData(uint8_t *data_ptr) {
  // This is initializing the modem to get ready for sending/receiving data.
  //"waking modem up"
  Serial.println("Waking up module");
  err = modem.begin();
  // Different Debugging info  
  if (err != ISBD_SUCCESS) {      
    Serial.print("Begin failed: error ");          
    Serial.println(err);
    if (err == ISBD_NO_MODEM_DETECTED) {
      Serial.println("No modem detected: check wiring.");
    } 
  } else if (err == ISBD_SUCCESS) {
    Serial.println("Modem.begin success");
  }
  delay(500);

  // Grabbing signal quality and printing it
  //delay(5000);
  err = modem.getSignalQuality(signalQuality);
  //delay(5000);
  // Different Debugging info
  if (err != ISBD_SUCCESS) {
    Serial.print("SignalQuality failed: error ");
    Serial.println(err);
    return;
  }
  Serial.print("On a scale of 0 to 5, signal quality is currently ");
  Serial.print(signalQuality);
  Serial.println(".");
  REDoff();
  YELLOWoff();
  for (int i = 1; i <= signalQuality; i++) { //non invasive debugging of signal quality
     delay(250);
     YELLOWon();
     delay(250);
     YELLOWoff();
  }
  
  if (signalQuality == 0) {
    REDblink();
  }

  //--------------------------------------------------------------------------------------------//
  //Sending data
  Serial.println("Waiting 50 seconds for capacitor to charge");
  delay (50000);
  Serial.println("Attempting to send data...");
  // The function modem.sendSBDBinary requires a pointer to an unsigned 8-bit array as the input.
  // We call the send data function with the input being our pointer to the array that now holds all of our data in 8-bit unsigned form.
  Serial.print("Err Before: ");
  Serial.println(err);
  modem.sendSBDBinary(data_ptr, data_array_size);
  err = 0;
  Serial.print("Err After: ");
  Serial.println(err);   
  // Different Debugging info
  if (err != ISBD_SUCCESS) {
    Serial.print("tried sending didnt work : ");
    if (err == ISBD_SENDRECEIVE_TIMEOUT) {
      Serial.println("Try again with a better view of the sky.");
    } else {
      Serial.print("Error Code: ");
      Serial.println(err);
    }
  } else if (err == ISBD_SUCCESS) {
    Serial.println("Data Sent");
  }
  return err;
}

//*****************************************************************************************************************************************************//
//These functions are for non-invasive debugging
void REDon() { digitalWrite(RED_PIN, LOW); }
void REDoff() { digitalWrite(RED_PIN, HIGH); }
void REDblink() {
  REDon();
  delay(250);
  REDoff();
  delay(250); 
  REDon();
  delay(250);
  REDoff();
  delay(250);
}
void YELLOWon(){ digitalWrite(YELLOW_PIN, LOW); }
void YELLOWoff() { digitalWrite(YELLOW_PIN, HIGH); }
void YELLOWblink() {
  YELLOWon();
  delay(250);
  YELLOWoff();
  delay(250);
  YELLOWon();
  delay(250);
  YELLOWoff();
}
void GREENon() { digitalWrite(GREEN_PIN, LOW); }
void GREENoff() { digitalWrite(GREEN_PIN, HIGH); }
void GREENblink() {
  GREENon();
  delay(250);  
  GREENoff();
  delay(250);
  GREENon();
  delay(250);  
  GREENoff();
  delay(250);
}

//*************************************************************************************************************************************************************//
char safeChar(float tmp) {
  if (tmp < 0) {
    tmp = 0;    
  } else if (tmp > 255) {
    tmp = 255;
  }
  return char(tmp);
}

//*****************************************************************************************************************************************************//
// These can be used for some extra debugging/diagnostics
// Both functions are REQUIRED in the code in order for the library to be utilized, even if they aren't used directly.
void ISBDConsoleCallback(IridiumSBD *device, char c) {
  #if DIAGNOSTICS
    Serial.write(c);
  #endif
}

void ISBDDiagsCallback(IridiumSBD *device, char c) {
  #if DIAGNOSTICS
    Serial.write(c);
  #endif
}

//*********************************************************************************************************************************************************//
/*
   This section of code is used to setup the Serial Moniter, RockBlock, weight sensors, rtc, and SD card
*/
void setup() {
  Serial.begin(9600);
  // --------ROCKBLOCK SECTION:
  //Start the serial port connected to the satellite modem
  IridiumSerial.begin(19200);
  data[0] = STATION_NUMBER;                    //First Byte of array is the station #
  for (int i = 1; i < 48; i++) { //initialize data array
    data[i] = 0;
  }
  data[44] = sample_pos;

  //  if (! IridiumSerial.begin(19200))
  //  {
  //    Serial.println(F("Sat Problem: Could not establish connection to modem"));
  //    return;
  //  }
  //  Serial.println(F("RockBlock Connected and Ready"));

  // --------WEIGHT SENSORS SECTION
  //initialize scale
  /*scale.set_scale(scale_calibration_factor);
    scale.tare(); //Reset the scale to 0
    scale_weight = scale.get_units();*/

  // --------BATTERY VOLTAGE AND PANEL CURRENT SECTION
  battery_voltage = analogRead(BATTERY_MONITOR) * V_SNSR_ADC_TO_V_SLOPE + V_SNSR_ADC_TO_V_INTCPT;
  panel_current = analogRead(PANEL_CURRENT) * I_SNSR_ADC_TO_A_SLOPE + V_SNSR_ADC_TO_V_INTCPT;

  // --------REAL TIME CLOCK SECTION:
  //Initiate the I2C bus and the RTC
  Wire.begin();
  rtc.begin();

  if (!rtc.begin()) {
    Serial.println("Couldn't find RTC");
    while (1);
  }
  
  //If RTC is not running, set it to the computer's compile time
  if (!rtc.initialized()) {
    Serial.println(F("RTC is NOT running!"));
  }
  //rtc.adjust(DateTime(2019, 6, 5, 6, 50, 0)); //year, month, day, hour, minute, second
  
  // --------SD CARD SECTION:
  //Initialize SD card
  if (!SD.begin(CS_PIN)) {
    Serial.println(F("SD Card Problem: Failure to begin connection"));
    //return;
  }
  Serial.println(F("SD Card Ready"));
  //Write column headers
  File dataFile = SD.open("WS6_FT2.csv", FILE_WRITE);
  if (dataFile) {
    dataFile.println(F("New Log Started!"));
    dataFile.println(F("Date,Time,Battery_Voltage(V),Panel_Current(A),Weight (lbs),Temperature(C),Temperature(F),Humidity(%),Active"));
    dataFile.close();                                   //Data isn't actually written until we close the connection!

    //Print same thing to the screen for debugging
    Serial.println(F("\nNew Log Started!"));
    Serial.println(F("Date,Time,Battery_Voltage(V),Panel_Current(A),Weight (lbs),Temperature(C),Temperature(F),Humidity(%),Active"));
  } else {
    Serial.println(F("Couldn't open log file on SD Card"));
  }
  // ------DEBUGGING SECTION:
  //Non-invasive debugging initialization
   pinMode(GREEN_PIN,OUTPUT);
   pinMode(YELLOW_PIN,OUTPUT);
   pinMode(RED_PIN,OUTPUT);
   pinMode(SAT_SEND_PIN,INPUT);
   GREENoff();
   GREENblink();
   YELLOWoff();
   YELLOWblink();
   REDoff();
   REDblink();
   debugging_flag = false;
   Serial.println("Starting the Main Loop");
}
//*********************************************************************************************************************************************************//
/*
   This section is the main loop of the program. It checks the battery voltage/current and water weight.
   After checking these values it proceedes to sendTimer() function, which checks if it should save
   the collected data to the SD card and/or send it using the satellite module.
*/
void loop() {
  // --------Voltage Sensor
  battery_voltage = analogRead(BATTERY_MONITOR) * V_SNSR_ADC_TO_V_SLOPE + V_SNSR_ADC_TO_V_INTCPT;    //check battery voltage

  // --------Current Sensor
  panel_current = analogRead(PANEL_CURRENT) * I_SNSR_ADC_TO_A_SLOPE + I_SNSR_ADC_TO_A_INTCPT;        //check solar panel current

  // --------Weight Sensor
  //check weight FC2231 Version
  //returns the calibrated weight in (lbs)
  weight = ((analogRead(WEIGHT_SENSOR1) + analogRead(WEIGHT_SENSOR2) + analogRead(WEIGHT_SENSOR3)) * FC2231_ADC_TO_LBS_SLOPE)/3 + FC2231_ADC_TO_LBS_INTCPT;
  weight = weight - BARREL_WGHT; //correct for barrel weight

  /*//check weight HX711 Version
    scale_weight = scale.get_units();
    if (abs(scale_weight) >= weight_difference_trigger) {
    weight = weight + scale_weight;
    }
    scale.tare(); */
  //---------Values for debugging
  //battery_voltage = 13.2;    //debugging values
  //panel_current = 1500;    //debugging values
  //weight = -30;    //debugging values
    
  // --------RTC section:
  //Check the time to send/save information
  checkTime(&sat_old_minute, &SD_old_minute, &sat_send_flag, &sat_save_flag, &SD_save_flag, &sat_sent_hr, &sat_save_min, &SD_save_min, alarms_triggered, initialized);
  
  // --------Save to data array
  if (sat_save_flag) {
    //check sat flag to update data array index
      sat_save_flag = false;
      Serial.println("Saving to Array"); 
      /*if (alarms_triggered || ((panel_current >= HIGH_I_TRIG) || (weight >= HIGH_WGHT_TRIG) || (weight <= LOW_WGHT_TRIG) ||
                        (battery_voltage >= HIGH_V_TRIG))){     // || (battery_voltage <= LOW_V_TRIG))) {*/
      //check alarms
      if (alarms_triggered ||((weight >= HIGH_WGHT_TRIG) || (weight <= LOW_WGHT_TRIG))) {
      data[1] = 7;
        //check which alarm was triggered
        /* 
        if(weight <= LOW_V_TRIG) {
          data[1] = 5; 
        }
        if(panel_current >= HIGH_I_TRIG) {
          data[1] = 4;
        }
        if(battery_voltage >= HIGH_V_TRIG) {
          data[1] = 6;
        } */
        if(weight >= HIGH_WGHT_TRIG) {
          data[1] = 3;
        }
        if(weight <= LOW_WGHT_TRIG) {
          data[1] = 1; 
          if(weight < -20.0) {
            data[1] = 2;
          }
        }
      } else {
        data[1] = 0; //no alarms triggered and all alarms reset
      }
      
      //store station parameters into data array
      data[2 + (sample_pos * 3)] = safeChar(weight);
      data[2 + (sample_pos * 3) + 1] = safeChar(panel_current/10);
      data[2 + (sample_pos * 3) + 2] = safeChar(battery_voltage*10);
      data[44] = sample_pos; //store the location of the most recent sample
      
      sample_pos++;             //increment the index by 1
      if (sample_pos >= 14) {
        sample_pos = 0;         //resets the index so it wraps around
      }
      
      DateTime datetime = rtc.now();
      days  = datetime.day();
      hours  = datetime.hour();
      minutes = datetime.minute();
      seconds = datetime.second();
      Serial.print("Saving to Array (Debugging Version) time:");
      Serial.print(days);
      Serial.print("=>");
      Serial.print(hours);
      Serial.print(":");
      Serial.print(minutes);
      Serial.print(":");
      Serial.print(seconds);
      Serial.print(":");
      Serial.print("Writing to indexes:");
      Serial.print(2 + ((sample_pos-1) * 3));
      Serial.print(",");
      Serial.print(2 + ((sample_pos-1) * 3)+1);
      Serial.print(",");
      Serial.println(2 + ((sample_pos-1) * 3)+2);
      YELLOWblink();
  }
  initialized = 0;    // Set during bootup to send data immediately, reset here to only send data at set time intervals "morn_time", "night_time"
  //Serial.println((String)"Main loop before sat_send_flag"+alarms_triggered);

  //debugging code
  if((!alarms_triggered && ((panel_current >= HIGH_I_TRIG) || (weight >= HIGH_WGHT_TRIG) || (weight <= LOW_WGHT_TRIG) ||
                        (battery_voltage >= HIGH_V_TRIG)))) {    // || (battery_voltage <= LOW_V_TRIG)))){
                          Serial.println("SECOND PART OF SAT SEND TRIGGERING");
                        }
  
  /*if (sat_send_flag || (!alarms_triggered && ((panel_current >= HIGH_I_TRIG) || (weight >= HIGH_WGHT_TRIG) || (weight <= LOW_WGHT_TRIG) ||
                        (battery_voltage >= HIGH_V_TRIG)))){            //|| (battery_voltage <= LOW_V_TRIG)))) {*/ //Full alarms (unimplemented)
                        
  if (sat_send_flag || (!alarms_triggered && ((weight >= HIGH_WGHT_TRIG) || (weight <= LOW_WGHT_TRIG)))) {  
    //check satellite flags and alarm levels to send data through satellite module
    sat_send_flag = false;
    SD_save_flag = true; //force save to SD card
    //check alarms
    if(alarms_triggered ||((weight >= HIGH_WGHT_TRIG) || (weight <= LOW_WGHT_TRIG))){
    data[1] = 7;
      //check which alarm was/is triggered 
      /*if(battery_voltage <= LOW_V_TRIG) {
        data[1] = 5; 
      }
      if(panel_current >= HIGH_I_TRIG) {
        data[1] = 4;
      }
      if(battery_voltage >= HIGH_V_TRIG) {
        data[1] = 6;
      } */
      if(weight >= HIGH_WGHT_TRIG) {
        data[1] = 3;
      }
      if(weight <= LOW_WGHT_TRIG) {
        data[1] = 1; 
        if(weight < -20) {
          data[1] = 2;
        }
      }
    } else {
      data[1] = 0;
    }

    //save most recent values to data array
    data[45] = safeChar(weight);
    data[46] = safeChar(panel_current/10);
    data[47] = safeChar(battery_voltage*10);
      
    if(!debugging_flag) {            //put back to !debugging_flag
      GREENon();
      //This sends the data, saving the err from the modem.sendSBDText function as the output
      // If the function outputs anything other than a success it tries to send the data again
      //FUTURE work will be having a time out for the data transmission not based on signal strength
      uint8_t *data_ptr = &data[0];
      Serial.println("Attempting to Send Data");
      
        //********** Will transmit data contonuously until it sends**************//
        int error = sendingData(data_ptr);
        delay(5000);
        while (error != ISBD_SUCCESS) {
          error = sendingData(data_ptr);       //call by reference the data
          delay(5000);
        }
        
        Serial.println("Data has just been sent by the modem");
        //Put modem to sleep after sending data
        Serial.println("Putting modem to sleep.");
        err = modem.sleep();
        if (err != ISBD_SUCCESS) {
          Serial.print("sleep failed: error ");
          Serial.println(err);
        }
        GREENoff();
    } else {
      DateTime datetime = rtc.now();
      days  = datetime.day();
      hours  = datetime.hour();
      minutes = datetime.minute();
      seconds = datetime.second();
      Serial.print("Attempting to Send Data (Debugging Version) Time:");
      Serial.print(days);
      Serial.print("=>");
      Serial.print(hours);
      Serial.print(":");
      Serial.print(minutes);  
      Serial.print(":");
      Serial.print(seconds);
      Serial.println(":");
      GREENblink();
    }
  }
  
  if (SD_save_flag) {
    //check SD flag to write to SD card.
    //if(!debugging_flag) {
      //Serial.print("Debugging Version: Saving to SD card "); 
      Serial.println("Saving Data to SD card");
      SD_save(battery_voltage, panel_current, weight);
    //} else {
      /* DateTime now = rtc.now();
      days  = now.day();
      hours  = now.hour();
      minutes = now.minute();
      seconds = now.second();
      Serial.print("Saving to SD card (Debugging Version) Time:");
      Serial.print(days);
      Serial.print("=>");
      Serial.print(hours);
      Serial.print(":");
      Serial.print(minutes);
      Serial.print(":");
      Serial.print(seconds);
      Serial.print(":Values(Weight,V,I)");
      Serial.print(weight);
      Serial.print(",");
      Serial.print(battery_voltage);
      Serial.print(",");
      Serial.print(panel_current);
      Serial.print("::sat_send_flag:");
      Serial.println(sat_send_flag); */
      REDblink();
    //}
    SD_save_flag = false;
  }
  
 /* Serial.println("checking ALARM RESET AND TRIGGER");
  Serial.println(panel_current); 
  Serial.println(HIGH_I_RST);
  Serial.println(weight);
  Serial.println(HIGH_WGHT_RST);
  Serial.println(weight);
  Serial.println(LOW_WGHT_RST);
  Serial.println(battery_voltage);
  Serial.println(HIGH_V_RST);
  Serial.println(battery_voltage);
  Serial.println(LOW_V_RST);
  delay(5000);*/
 
  // --------ALARM TRIGGER AND RESET:  (done this way to prevent bouncing between states)
  /*if ((panel_current <= HIGH_I_RST) && (weight <= HIGH_WGHT_RST) && (weight >= LOW_WGHT_RST) &&
      (battery_voltage <= HIGH_V_RST) && (battery_voltage >= LOW_V_RST)) {*/
  if ((weight <= HIGH_WGHT_RST) && (weight >= LOW_WGHT_RST)) {
        //Serial.println("Alarm reset");
    alarms_triggered = false;    //reset
  }

  /*if ((panel_current >= HIGH_I_TRIG) || (weight >= HIGH_WGHT_TRIG) || (weight <= LOW_WGHT_TRIG) ||
      (battery_voltage >= HIGH_V_TRIG)){        // || (battery_voltage <= LOW_V_TRIG)) {*/
  if ((weight >= HIGH_WGHT_TRIG) || (weight <= LOW_WGHT_TRIG)) {
        //Serial.println("Alarm triggered");
    alarms_triggered = true;     //trigger
  }
}
