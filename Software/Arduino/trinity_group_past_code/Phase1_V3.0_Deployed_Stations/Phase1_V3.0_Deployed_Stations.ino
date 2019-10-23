// V3.0 of Deployed Stations Code for Trinity Water Stations Project
// Authors: Nathan Richter
// Based on V2.2 of Deployed Stations Code for Trinity Water Stations Project by. Brady Burns,Brian Guenther, and Zach
// Last Update 5/27/2019
// Its purpose is to read 3 weight sensors, convert it to weight and then send this via satellite every twelve hours.
/* Requirements:
 * Irridium SBD Library installed, Version of Arduino must be 1.6.21, Arduino MEGA, RockBLOCK V2.c, 4 Weight Sensors
*/
/* Wiring:
 * Arduino 5V -> RB 5VIN, Arduino GND -> RB GND, Arduino GPIO 4 -> RB ON/OFF, Arduino TX3 (GPIO 14) -> RB TX, Arduino RX3 (GPIO 15) -> RB RX, Weight Sensors -> A0-A3, 3.3V -> A4, 5V/GND to 5V/GND on weight sensors.
 * NOTE: Read to Read and write to write
*/  
// For more details on any of these requirements/setup instructions/Wiring Diagram see Supplemental

//**********************************************************************************************************************************************************//
//Include libraries
#include <IridiumSBD.h> //Library used to communicate with RockBLOCK Module

//Station Identifiers
const uint8_t STATION_NUMBER = 1;
const char    ROCKBLOCK_NUMBER[] = "300234067431270";

//Debugging
#define DIAGNOSTICS false // Change this to see diagnostics (unimplemented)

// Rockblock error handling
int signalQuality = -1; // used for testing signal strength
int err;                // Used for status of built in functions of library

// Declare the Rockblock with an IridiumSBD object (Initializing Satellite communication with on/off pin and serial pins)
#define IridiumSerial Serial3  // Rx15 and Tx 14 -> NOTE: If you aren't using a MEGA you will probably have to change this.
const int SLEEP_PIN = 4;       //This pin is used to turn satellite module on/off
IridiumSBD modem(IridiumSerial, SLEEP_PIN);

// Define analog pins 
const int Sensor_0 = A0; //Weight sensors 
const int Sensor_1 = A1;  
const int Sensor_2 = A2;
const int Sensor_ref = A8; //This is just the 3.3V wired to the ADC so we have a reference/control to make sure that the ADC is working as expected

// Calibration Curve
const float FC2231_ADC_TO_LBS_SLOPE = 0.37;        //slope for ADC to lbs calibration curve
const float FC2231_ADC_TO_LBS_INTCPT = -41.5;      //y-intercept for ADC to lbs calibration curve

const float BARREL_WGHT = 36.4;                    //weight of the water barrel and the shelving unit (in lbs)

//initialize the array for storing satellite transmission data
const size_t data_array_size = 48;                 //size of the transmission data array
uint8_t data[data_array_size];

// Alarms set and reset values
const float LOW_WGHT_TRIG = 25.02; //low weight trigger (in lbs)
const float LOW_WGHT_RST = 110;    //reset for the low weight alarm (in lbs)
int alarms_triggered = 0;          //alarms are unset on power up

//Used as state indicator to do test send when first powered on/rebooted
int init_const = 0;

//Initialize Arrays
int data_avg[5];
float data_weight[5];
//**********************************************************************************************************************************************************//

//**********************************************************************************************************************************************************//
void writingData(uint8_t *data, int index) {
  // This function reads each weight sensor and then updates the data array with the values.
  /* INPUTS
   * Data: must be char array and be 5 length.
   * Index: must be integer
   * 
   * OUTPUTS
   * NONE
  */
   
  /* OPERATION
   *  This function reads each weight sensor and ref votlage 800 times, then takes the average of each (called sampled_n). 
   *  Next, we output these values to the data array, positioning them in the array based on the index variable. If you pass in an index of 5, then the function puts
   *  sampled_0 at data[5], sampled_1 at data[6], etc. 
   *  NOTE: because C++ can't return an array, we simply change the values of the input array. 
   *  NOTE: This array must have already been initialized before calling this function.
   *  
  */
  //Accumulators used to hold sums for multisampling (unsigned 32 bit integers because theoretically they could be as large as 100,000 each).
  uint32_t sum_0 = 0; 
  uint32_t sum_1 = 0;
  uint32_t sum_2 = 0;
  uint32_t sum_ref = 0;
  char tmp = 0;
  
  //Multisampling each weight sensor and reference
  for(int i=0;i<800;i++) {
    int analog_0 = analogRead(Sensor_0);
    sum_0 += analog_0;
    int analog_1 = analogRead(Sensor_1);
    sum_1 += analog_1;
    int analog_2 = analogRead(Sensor_2);
    sum_2 += analog_2;
    int analog_ref = analogRead(Sensor_ref);
    sum_ref += analog_ref;
  }

  //Average sample.
  uint32_t sampled_0   = sum_0/800;
  uint32_t sampled_1   = sum_1/800;
  uint32_t sampled_2   = sum_2/800;
  uint32_t sampled_ref = sum_ref/800;
  
  tmp = map(sampled_0,0,1023,0,255);
  data[index] = tmp;
  tmp = map(sampled_1,0,1023,0,255);
  data[index+1] = tmp;
  tmp = map(sampled_2,0,1023,0,255);
  data[index+2] = tmp;
  tmp = map(sampled_ref,0,1023,0,255);
  data[index+3] = tmp;
  float tmp2 = (((sampled_0+sampled_1+sampled_2)/3)*FC2231_ADC_TO_LBS_SLOPE+FC2231_ADC_TO_LBS_INTCPT-BARREL_WGHT);
  
  data[index+4] = safeChar(tmp2);
}
//**********************************************************************************************************************************************************//

//**********************************************************************************************************************************************************//
//Same as Above function but returns an array of averages (this is really only used for debugging/calibrating)
void readingDataAvg(int (& data_avg) [5], int index) {
  //Constants used to hold sums for multisampling
  // These are declared as unsigned 32 bit integers because theoretically they could be as large as 100,000 each.
  // Additionally, it is impossible for the ADC to output a negative number
  uint32_t sum_0 = 0; 
  uint32_t sum_1 = 0;
  uint32_t sum_2 = 0;

  //Multisampling each weight sensor and reference
  for(int i=0;i<800;i++) {
    int analog_0 = analogRead(Sensor_0);
    sum_0 += analog_0;
    int analog_1 = analogRead(Sensor_1);
    sum_1 += analog_1;
    int analog_2 = analogRead(Sensor_2);
    sum_2 += analog_2;
  }
  uint32_t sampled_0 = sum_0/800;
  uint32_t sampled_1 = sum_1/800;
  uint32_t sampled_2 = sum_2/800;
  uint32_t sampled_avg = (sampled_0+sampled_1+sampled_2)/3;
  data_avg[index] = sampled_avg;
} 

//Same as Above function but returns an array of weights instead of raw values (this is really only used for debugging/calibrating)
void readingDataWeight(float (& data_weight) [5], int index) {
  //Constants used to hold sums for multisampling
  // These are declared ass unsigned 32 bit integers because theoretically they could be as large as 100,000 each.
  // Additionally, it is impossible for the ADC to output a negative number (hopefully)
  uint32_t sum_0 = 0; 
  uint32_t sum_1 = 0;
  uint32_t sum_2 = 0;

  //Multisampling each weight sensor and reference
  for(int i=0;i<800;i++) {
    int analog_0 = analogRead(Sensor_0);
    sum_0 += analog_0;
    int analog_1 = analogRead(Sensor_1);
    sum_1 += analog_1;
    int analog_2 = analogRead(Sensor_2);
    sum_2 += analog_2;
  }
  uint32_t sampled_0   = sum_0/800;
  uint32_t sampled_1   = sum_1/800;
  uint32_t sampled_2   = sum_2/800;
  float sampled_weight = ((((sampled_0+sampled_1+sampled_2)/3)*FC2231_ADC_TO_LBS_SLOPE+FC2231_ADC_TO_LBS_INTCPT-BARREL_WGHT));
  data_weight[index]   = sampled_weight;
} 
//*************************************************************************************************************************************************************//

//*************************************************************************************************************************************************************//
int sendingData(uint8_t *data_ptr) {
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
   * Sending Data: First converts the int array into a string, adding extra zeros so that each sensor reading is represented by three digits. The reason we do this is so we can then cast this string into a char array that is accepted by the sendSBDText function. This is pretty convoluted but we were working on short time budget.
   * Next, we create a pointer to the beginning of our char array (This is the required input to the sendSBDText function).
   * Then we Call the function, and have some options for debugging info.
   * For more info on the SBDsendText function see the Readme which has some helpful documents.
  */
  //--------------------------------Initalize the Rockblock--------------------------------------//
  // Initialize the modem to get ready for sending/receiving data.
  Serial.println("Waking up module");
  err = modem.begin();
  //Check to make sure the module woke up.  
  if (err != ISBD_SUCCESS){      
    Serial.print("Begin failed: error ");          
    Serial.println(err);
    //Check to see if there is even a Rockblock connected to the controller.
    if (err == ISBD_NO_MODEM_DETECTED){
      Serial.println("No modem detected: check wiring.");
    } 
  }
  else if(err == ISBD_SUCCESS){
    Serial.println("Modem.begin success");
  }
  delay(500);

  //Get signal quality and print it
  err = modem.getSignalQuality(signalQuality);
  delay(5000);
  //Check to see if the controller was able to get the signal quality.
  if (err != ISBD_SUCCESS){
    Serial.print("SignalQuality failed: error ");
    Serial.println(err);
    return err;
  }
  Serial.print("On a scale of 0 to 5, signal quality is currently ");
  Serial.print(signalQuality);
  Serial.println(".");
  //-----------------------------------Sending the Data------------------------------------------//
  Serial.println("Waiting 50 seconds for capacitor to charge");
  delay (50000);
  Serial.println("Attempting to send data...");

  // NOTE: A credit is spent for every 50 bytes of data (rounded up to the nearest 50) sent using the modem.sendSBDBinary function. (i.e 1-50 bytes will cost 1 credit, 51-100 will cost 2 credits, etc.)
  // Finally, we call the sendSBDBinary function with the input being our pointer to the data array.
  Serial.print("Err Before: ");
  Serial.println(err);
  err = modem.sendSBDBinary(data_ptr, data_array_size);
  err = ISBD_SUCCESS;
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
//*************************************************************************************************************************************************************//

//*************************************************************************************************************************************************************//
char safeChar(float tmp) {
  if (tmp < 0) {
    tmp = 0;    
  } else if (tmp > 255) {
    tmp = 255;
  }
  return char(tmp);
}
//*************************************************************************************************************************************************************//

//*************************************************************************************************************************************************************//  
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
//*************************************************************************************************************************************************************// 

//*************************************************************************************************************************************************************//
void setup(){
  // Start the console serial port
  Serial.begin(115200);
  while (!Serial); //wait for port to start up
  IridiumSerial.begin(19200);    // Start the serial port connected to the satellite modem
  data[0] = STATION_NUMBER;      //First Byte of array is the station #
  data[1] = 0;                   //Second Byte of array is the alarm. 
  for (int i = 2; i < 47; i++) { //initialize data array
    data[i] = 0;
  }
}
//*************************************************************************************************************************************************************//

//*************************************************************************************************************************************************************//
// This is the main loop that runs on repeat
void loop() {    
  uint8_t *data_ptr = &data[0]; //define pointer to the array
  //This loop is meant to run when first powered on/rebooted. 
  if(init_const == 0) {
    for (int i=2;i<42;i+=5) { //fill data array
      writingData(data_ptr,i);
      delay(100);
    }
    
    for(int j =0;j<48;j++) { //print the data array
      Serial.print(data[j]);
      Serial.print(",");
    }
    Serial.println();
    
    for(int b=0; b<5; b++) {
      readingDataAvg(data_avg,b);
      delay(100);
    }
    
    for(int j =0; j<5; j++) {  //Print the average value from the data array
      Serial.print(data_avg[j]);
      Serial.print(",");
    }
    Serial.println();
    
    for(int b=0; b<5; b++) {
      readingDataWeight(data_weight,b);
      delay(100);
    }
    
    for(int j =0; j<5; j++) { //Print the weight data
      Serial.print(data_weight[j]);
      Serial.print(",");
    }
    Serial.println();
    
    int sampled_0 = analogRead(Sensor_0); //sample each sensors
    int sampled_1 = analogRead(Sensor_1);
    int sampled_2 = analogRead(Sensor_2);
    float tmp_weight = (((sampled_0+sampled_1+sampled_2)/3)*FC2231_ADC_TO_LBS_SLOPE+FC2231_ADC_TO_LBS_INTCPT-BARREL_WGHT);
   
    if(tmp_weight < LOW_WGHT_TRIG) { //check if low weight alarm should be triggered
      data[1] = 1;
      if(tmp_weight <=-20) {
        data[1] = 2;
      }
    }
     
    data[45] = safeChar(tmp_weight);
    
    int test_error = sendingData(data_ptr); //Try Once
    delay(5000);
  
  //    while(test_error != ISBD_SUCCESS)
  //    {
  //      test_error = sendingData(data);
  //      delay(5000);
  //    }
  
    init_const = 1;
  }
  
  //Put modem to sleep after sending data
  Serial.println("Putting modem to sleep.");
  err = modem.sleep();
  if(err != ISBD_SUCCESS) {
    Serial.print("sleep failed: error ");
    Serial.println(err);
  }
  
  //Clear Data$ Alarm After Initial Send
  for(int i = 1; i <= 47; i++) { //reset data array
    data[i] = 0;
  }
  
  //This loop fills the array with data, and then once full it sends it 
  for(int i=2; i<42; i+=5) {
    writingData(data_ptr,i);
    
    //Print the data being saved into the data array after each iteration of the loop
    for(int j =0; j<48; j++) {
      Serial.print(data[j]);  
      Serial.print(",");
    }
    Serial.println();
    delay(5400000); //Wait 90 minutes, this causes data to be sent approximately once every 12 hours as the loop iterates 8 times
    //delay(60000); //Wait 60s (for testing)
  } 
  
  //Fill the last index with the current weight
    int sampled_0 = analogRead(Sensor_0);
    int sampled_1 = analogRead(Sensor_1);
    int sampled_2 = analogRead(Sensor_2);
    float tmp_weight = (((sampled_0+sampled_1+sampled_2)/3)*FC2231_ADC_TO_LBS_SLOPE+FC2231_ADC_TO_LBS_INTCPT-BARREL_WGHT);
    
    if(tmp_weight < LOW_WGHT_TRIG) { //check if low weight alarm should be triggered
      data[1] = 1;
      if(tmp_weight <=-20) {
        data[1] = 2;
      }
    }
     
    data[45] = safeChar(tmp_weight); //store most recent weight 
  
  for(int j =0;j<48;j++) { //print data to be transmitted
    Serial.print(data[j]);  
    Serial.print(",");
  }
  Serial.println();
  
  //This sends the data, saving the err from the modem.sendSBDBinary function as the output
  //If the function outputs anything other than a success it tries to send the data again
  int error = sendingData(data_ptr);
  delay(5000);
  while(error != ISBD_SUCCESS) { //keep trying to transmit via satellite (NO TIMEOUT)
    error = sendingData(data_ptr);
  delay(5000);
  }
  
  //Put modem to sleep after sending data
  Serial.println("Putting modem to sleep.");
  err = modem.sleep();
  if (err != ISBD_SUCCESS) {
    Serial.print("sleep failed: error ");
    Serial.println(err);
  }
}
//*************************************************************************************************************************************************************//
