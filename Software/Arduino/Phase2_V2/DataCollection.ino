//////////////////////////////////////////////////////////////////////////////
// Serial Handling

void serialFlush(){

  /*
  This function clears all the entered character's in the
  Serial buffer. This function is used to allow the
  while(Serial.avaliable() == 0){} to effectively wait
  for the user's command.
  */

  while(Serial.available() > 0){
    char t = Serial.read();
  }
}

void serialObtainNumber(){

  /*
  This function obtains the value of the given weight value from
  Serial.
  */

  while(Serial.available() == 0){}
  placed_test_weight = Serial.parseFloat();

  Serial.print("PLACED TEST WEIGHT VALUE: ");
  Serial.print(placed_test_weight, 5);
  Serial.println(" (lbs)");

}

void printDataArray(){

  /*
  This function just provides the necessary format to printout
  all the data contained within the data array.
  */

  Serial.println();
  Serial.println("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@");
  Serial.println("Printing Complete Array Values");

  // Station Information
  Serial.print("[0]: Station Number: ");
  Serial.println(data_pointer[0]);

  // Alarm Values
  Serial.print("[1]: Alarms: ");
  Serial.println(data_pointer[1]);

  int set_counter = 1;
  for (int index = 2; index < DATA_ARRAY_SIZE - (2 + 5); index += 5){

    // Set Index Printing
    Serial.println();
    Serial.print("******** ");
    Serial.print("(");
    Serial.print(set_counter);
    Serial.print(" / 8)");
    Serial.println(" ********");

    // Value Printing
    Serial.print("[");
    Serial.print(index);
    Serial.print("]: Sensor 1: ");
    Serial.println(data_pointer[index]);

    Serial.print("[");
    Serial.print(index + 1);
    Serial.print("]: Sensor 2: ");
    Serial.println(data_pointer[index + 1]);

    Serial.print("[");
    Serial.print(index + 2);
    Serial.print("]: Sensor 3: ");
    Serial.println(data_pointer[index + 2]);

    Serial.print("[");
    Serial.print(index + 3);
    Serial.print("]: Reference: ");
    Serial.println(data_pointer[index + 3]);

    Serial.print("[");
    Serial.print(index + 4);
    Serial.print("]: Weight: ");
    Serial.println(data_pointer[index + 4]);

    set_counter++;
  }

  Serial.println("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@");
}

//////////////////////////////////////////////////////////////////////////////
// Calibration Routines

void zeroWeightCalibration(){

  /*
  This function collects the values of the sensor's output
  without any additional weight placed above the sensors. This
  helps us only calculate the weight actually placed above these
  values.
  */

  Serial.println("ZERO WEIGHT MEASUREMENT: PRESS ANY KEY TO TRIGGER");
  while(Serial.available() == 0){}
  serialFlush();
  Serial.println("ZERO WEIGHT MEASUREMENT: PERFORMING MEASUREMENT");

  // Obtaining the value of the weight sensors
  for (uint32_t i = 0; i < (sizeof(zero_weight_sensor_values) / sizeof(zero_weight_sensor_values[0])); i++){

    for (uint32_t j = 0; j < NUMBER_OF_SAMPLES; j++){
      zero_weight_sensor_values[i] += analogRead(WEIGHT_SENSORS_PINS[i]);
    }

    zero_weight_sensor_values[i] = zero_weight_sensor_values[i]/NUMBER_OF_SAMPLES; // Averaging Value
  }

  // Report of Zero Weight Measurement
  for (uint32_t i = 0; i < (sizeof(zero_weight_sensor_values) / sizeof(zero_weight_sensor_values[0])); i++){
    Serial.print("Sensor ");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(zero_weight_sensor_values[i]);
  }
}

void barrelWeightCalibration(){

  /*
  This function handles with the weighing of the barrel placed on top of
  the weight sensors. While still using a hard-coded value for the sensor's
  voltage output and lbs slope/ratio, the barrel weight calibration needs
  to happen before because the barrel provides the necessary platform to properly
  calculate the slope/ratio.
  */

  Serial.println("BARREL WEIGHT MEASUREMENT: PRESS ANY KEY TO TRIGGER");
  while(Serial.available() == 0){}
  serialFlush();
  Serial.println("BARREL WEIGHT MEASUREMENT: PERFORMING MEASUREMENT");

  // Obtaining the value of the weight sensors
  for (uint32_t i = 0; i < (sizeof(barrel_weight_sensor_values) / sizeof(barrel_weight_sensor_values[0])); i++){

    for (uint32_t j = 0; j < NUMBER_OF_SAMPLES; j++){
      barrel_weight_sensor_values[i] += analogRead(WEIGHT_SENSORS_PINS[i]);
    }

    barrel_weight_sensor_values[i] = barrel_weight_sensor_values[i]/NUMBER_OF_SAMPLES; // Averaging Value
    barrel_weight_sensor_value += barrel_weight_sensor_values[i] - zero_weight_sensor_values[i];
  }

  // Report of Zero Weight Measurement
  for (uint32_t i = 0; i < (sizeof(barrel_weight_sensor_values) / sizeof(barrel_weight_sensor_values[0])); i++){
    Serial.print("Sensor ");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(barrel_weight_sensor_values[i]);
  }

  barrel_weight = barrel_weight_sensor_value * ADC2LBS_SLOPE;
  Serial.print("Barrel Weight (with pre-set adc2lbs_slope value): ");
  Serial.println(barrel_weight);
}

void slopeCalibration(){

  /*
  This function handles the calibration of the slope between the sensor's value
  and the actual lbs placed on top of the sensor. This slope can also be considered
  as the ratio between sensor's voltage output and physical lbs of weight.
  */

  Serial.println("ADC2LBS_SLOPE MEASUREMENT: PRESS ANY KEY TO TRIGGER");
  while(Serial.available() == 0){}
  serialFlush();
  Serial.println("ADC2LBS_SLOPE MEASUREMENT: PERFORMING MEASUREMENT");

  Serial.println("ENTER PLACED TEST WEIGHT (LBS):");
  serialObtainNumber();
  serialFlush();

  // Obtaning the value of the weight sensors
  for (uint32_t i = 0; i < (sizeof(slope_weight_sensor_values) / sizeof(slope_weight_sensor_values[0])); i++){

    for (uint32_t j = 0; j < NUMBER_OF_SAMPLES; j++){
      slope_weight_sensor_values[i] += analogRead(WEIGHT_SENSORS_PINS[i]);
    }

    slope_weight_sensor_values[i] = slope_weight_sensor_values[i]/NUMBER_OF_SAMPLES; // Averaging Value
    slope_weight_sensor_value += slope_weight_sensor_values[i] - (barrel_weight_sensor_values[i]);
  }

  // Calculating the slope value
  Serial.print("Slope weight sensor value: ");
  Serial.println(slope_weight_sensor_value);

  adc2lbs_slope = placed_test_weight / slope_weight_sensor_value;

  // Report of ADC2LBS Slope Calibration
  Serial.print("ADC2LBS_SLOPE: ");
  Serial.println(adc2lbs_slope, 5);

  // Report of Barrel Weight with new ADC2LBS Slope value
  barrel_weight = barrel_weight_sensor_value * adc2lbs_slope;
  Serial.print("Barrel Weight (with calculated adc2lbs_slope value): ");
  Serial.println(barrel_weight);

}

void calibrationRoutine(){

  /*
  This function does the calibration routine, which collected the sensor
  values for Zero Weight and the Barrel Weight. These two sets of data is
  later used in the dataCollection functions to calculate the additional
  weight placed after the barrel.
  */

  Serial.println("WEIGHT SENSOR CALIBRATION");

  // ***********************
  // Zero Weight Calibration
  // ***********************

  zeroWeightCalibration();

  // *************************
  // Barrel Weight Calibration
  // *************************

  barrelWeightCalibration();

  // *************************
  // ADC2LBS Slope Calibration
  // *************************

  slopeCalibration();

}

//////////////////////////////////////////////////////////////////////////////
// Misc Functions

uint8_t safeChar(float variable){

  /*
  This function takes a float input, typically one of the main
  variables send within the data array, to ensure that the variable
  falls within the 8-bit value range (0-255).
  */
  
  uint32_t safe_variable = 0;
  if (variable > 255){
    safe_variable = 255;
  }
  else if (variable < 0){
    safe_variable = 0;
  }
  else{
    safe_variable = (uint32_t) variable;
  }

  return safe_variable;
}

void waitUntilTimePasses(float raw_delay_value, String delay_type){

  /*
  This function creates a customizable delay by using the
  rtc object. Once the specified quantity of time has passed,
  this function will be exited.
  */
  
  int days = 0;
  int hours = 0;
  int minutes = 0;
  int seconds = 0;
  
  if (delay_type == "days") days = raw_delay_value;
  else if (delay_type == "hours) hours = raw_delay_value;
  else if (delay_type == "seconds) second = raw_delay_value;
  else minutes = raw_delay_value;
  
  DateTime current_time = rtc.now();
  DateTime time_to_check_sensors (now + TimeSpan(days, hours, minutes, seconds));
  
  // Less than means older
  while(time_to_check_sensors < current_time){
    delay(1000);
  }
}

//////////////////////////////////////////////////////////////////////////////
// Single data collection and complete data collection

void saveSD(float weight, float voltage, float current){

  /*
  This function saves multiple sensor values to a on-board
  SD card for later troubleshooting, once the station is 
  collected.
  */

  DateTime time_now = rtc.now();

  int chk = dht_sensor.read11(DHT11_PIN); // I have no idea what this line does ??
  
  File data_file = SD.open(csv_filename, FILE_WRITE);
  
  if(data_file){
  
    data_file.print(time_now.timestamp(TIMESTAMP_DATE));
	data_file.print(F(","));
	data_file.print(time.now.timestamp(TIMESTAMP_TIME));
	data_file.print(F(","));
	data_file.print(voltage);
	data_file.print(F(","));
	data_file.print(current);
	data_file.print(F(","));
	data_file.print(weight);
	data_file.print(F(","));
	data_file.print(dht_sensor.temperature);
	data_file.print(F(","));
	data_file.print(dht_sensor.temperature * 1.8 + 32);
	data_file.print(F(","));
	data_file.print(dht_sensor.humidity);
	data_file.print(F(","));
	data_file.print("Active")
	data_file.close();
  }
  else Serial.println("SD save failed);

}

void dataCollection(int index){

  /*
  This function collects the data from the weight sensors, averages it according
  to the NUMBER_OF_SAMPLES variable, calculates the average weight of all sensors,
  and then calculates the weight of the jugs.
  */

  // Weight Sensor data collection
  uint32_t sensor_values[] = {0, 0, 0};

  // Obtaining the value of the weight sensors
  for (uint32_t i = 0; i < (sizeof(sensor_values) / sizeof(sensor_values[0])); i++){

    for (uint32_t j = 0; j < NUMBER_OF_SAMPLES; j++){
      sensor_values[i] += analogRead(WEIGHT_SENSORS_PINS[i]);
    }

    sensor_values[i] = sensor_values[i]/NUMBER_OF_SAMPLES; // Averaging Value
  }

  int accumulative_a2d_weight = 0;

  for (uint32_t k = 0; k < (sizeof(sensor_values) / sizeof(sensor_values[0])) - 1; k++){
    accumulative_a2d_weight += sensor_values[k] - barrel_weight_sensor_values[k];

  }

  // Calculating the weight from voltage to lbs (would prefer metric, but client wants imperial units >:S )
  float weight_value = accumulative_a2d_weight * adc2lbs_slope;

  // Voltage and Current data collection
  float battery_voltage_reading = analogRead(BATTERY_MONITOR);
  float battery_voltage = battery_voltage_reading * V_SNSR_ADC_TO_V_SLOPE + V_SNSR_ADC_TO_V_INTCPT;
  battery_voltage *= 10;
  float panel_current_reading = analogRead(PANEL_CURRENT);
  float panel_current = panel_current * I_SNSR_ADC_TO_A_SLOPE + V_SNSR_ADC_TO_V_INTCPT;
  panel_current /= 10;

  // Printing Raw Values for Debugging
  Serial.println();
  Serial.print("&&&&&&&& ");
  Serial.print("(");
  Serial.print((index - 2) / 5 + 1);
  Serial.print(" / 8)");
  Serial.println(" &&&&&&&&");
  Serial.println("Raw Sensor Values");

  for (uint32_t i = 0; i < (sizeof(sensor_values) / sizeof(sensor_values[0])); i++){
    Serial.print("Sensor ");
    Serial.print(i);
    Serial.print(": ");
    Serial.println(sensor_values[i]);
  }

  Serial.print("Accumulative A2D Weight Value: ");
  Serial.println(accumulative_a2d_weight);
  
  Serial.print("Battery Voltage Reading: ");
  Serial.println(battery_voltage_reading);
  
  Serial.print("Panel Current Reading: ");
  Serial.println(panel_current_reading);

  // Printing calculated values for debugging

  Serial.print("Weight Value: ");
  Serial.println(weight_value, 3);
  
  Serial.print("Battery Voltage [V]: ");
  Serial.println(battery_voltage);
  
  Serial.print("Panel Current [I]: ");
  Serial.println(panel_current);

  // Setting alarms for the only last weight value
  if (index == 41){ // Latest Weight Value Only
    data[1] = ALL_GOOD;
	alarms[] = {0,0,0};
	alarm_total_value = 0;

	// Weight Alarms
    if (weight_value < (-0.5 * barrel_weight)) alarms[0] = BARREL_REMOVED;
    else if (weight_value < LOW_WEIGHT_TRIGGER) alarms[0] = LOW_WEIGHT;
    else if (weight_value > 255) alarms[0] = HIGH_WEIGHT;
	
	// Voltage Alarms
	if (battery_voltage < LOW_VOLTAGE_TRIGGER) alarms[1] = LOW_VOLTAGE;
	else if (battery_voltage > HIGH_VOLTAGE_TRIGGER) alarms[1] = HIGH_VOLTAGE;
	
	if (panel_current > HIGH_CURRENT_TRIGGER) alarms[2] = HIGH_CURRENT;
	
	for (int i = 0; i < (sizeof(alarms) / sizeof(alarms[0])); i++){
	
	  if (alarms[i] == 0) continue;
	  else if (alarm_total_value == 0) alarm_total_value += alarms[i];
	  else alarm_total_value = alarm_total_value * 10 + alarms[i];
	}
	
	if (alarm_total_value > 100){ // Three alarms at the same time
	  data[1] = CHECK_STATION;
	}
	else data[1] = alarm_total_value;
  }
  
  // Capping and making variables fit within 8 bit margin (0-255)
  
  uint8_t safe_weight_value = safeChar(weight_value);
  uint8_t safe_voltage_value = safeChar(battery_voltage);
  uint8_t safe_current_value = safeChar(panel_current);
  

  // Rescaling values to fit within a byte
  for (int i = 0; i < (sizeof(sensor_values) / sizeof(sensor_values[0])); i++){
    sensor_values[i] = map(sensor_values[i], 0, 1023, 0, 255);
  }

  // Storing values into the data array
  data_pointer[index] = safe_weight_value; // Weight Value, duh
  data_pointer[index + 1] = safe_voltage_value;
  data_pointer[index + 2] = safe_current_value;
  
  // Saving to SD card
  saveSD(weight_value, battery_voltage, panel_current);

  // For the last weight measurement, we place the value onto the
  // 45:47 index as well
  
  if (index == 41){
    data_pointer[44] = 41;
    data_pointer[45] = data_pointer[41];
	data_pointer[46] = data_pointer[42];
	data_pointer[47] = data_pointer[43];
  }

}

void completeDataCollection(float raw_delay_value, String delay_type){

  /*
  This function handles with the data collection over a period of time,
  with a delay in-between measurements of 'minute_delay' minute(s) apart.
  
  Supposively the data should be collected every 50 minutes
  
  */

  for (int index = 2; index < DATA_ARRAY_SIZE - (2 + 3); index += 3){
    dataCollection(index);
    waitUntilTimePasses(raw_delay_value, delay_type);
  }

  printDataArray();
}