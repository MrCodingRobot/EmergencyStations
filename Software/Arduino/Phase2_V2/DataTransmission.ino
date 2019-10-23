//////////////////////////////////////////////////////////////////////////////
// rockBlock handling (setup and sleep)

void rockBlockSetup() {

  /*
  This function setups up the rockBLOCK. This accounts for the modem
  being turned on and while checking that the signal strength of the 
  rockBLOCK is acceptable.
  */
  
  Serial.println("ROCKBLOCK SETUP");
  int isbd_status_message = -1;

  while (isbd_status_message != ISBD_SUCCESS){
    Serial.println("Using modem.begin()");
    isbd_status_message = modem.begin();
    Serial.println("Done using modem.begin()");

    if (isbd_status_message == ISBD_SUCCESS){
      Serial.println("MODEM.BEGIN() SUCCESSFUL");
      break;
    }
  
    else{
      Serial.print("ISBD STATUS FAILURE - MESSAGE: "); 
      
      switch (isbd_status_message) {
      case ISBD_ALREADY_AWAKE:
        Serial.println("ISBD_ALREADY_AWAKE");
        break;
      case ISBD_SERIAL_FAILURE:
        Serial.println("ISBD_SERIAL_FAILURE");
        break;
      case ISBD_PROTOCOL_ERROR:
        Serial.println("ISBD_PROTOCOL_ERROR");
        break;
      case ISBD_NO_MODEM_DETECTED:
        Serial.println("ISBD_NO_MODEM_DETECTED");
        break;
      default:
        Serial.println("UNKNOWN ISBD ERROR");
        break;
      }
    
    Serial.println("MODEM.BEGIN() FAILED, TRYING AGAIN IN 30 SECONDS");
    delay(30000); // 1000 milliseconds = 1 second * 30 = 30 seconds
    
    }
  }

  // After modem.begin() success, now modem.getSignalQuality()
  
  int signal_quality = -1;
  
  isbd_status_message = modem.getSignalQuality(signal_quality);
  delay(5000); // 5 Seconds Delay

  while (isbd_status_message != ISBD_SUCCESS){
    Serial.print("SIGNAL QUALITY ERROR: ");
    Serial.println(isbd_status_message);

    Serial.println("MODEM.GETSIGNALQUALITY FAILED, TRYING AGAIN IN 15 SECONDS");
    delay(15000); // 1000 milliseconds = 1 second * 15 = 15 seconds
    isbd_status_message = modem.getSignalQuality(signal_quality);
  }

  Serial.print("On a scale of 0 to 5, signal quality: ");
  Serial.println(signal_quality);
}

void rockBlockSleep(){

  /*
  The purpose of this function is to turn of the
  rockBLOCK no matter the how long it takes.
  */
  
  Serial.println("PUTTING MODEM TO SLEEP");
  int isbd_status_message = -1;

  while (isbd_status_message != ISBD_SUCCESS){
    isbd_status_message = modem.sleep();

    Serial.print("ISBD STATUS MESSAGE: ");
    if (isbd_status_message == ISBD_SUCCESS){
      Serial.println("ISBD_SUCCESS");
    }
    else {
      Serial.println(isbd_status_message); 
    }
  }
}

//////////////////////////////////////////////////////////////////////////////
// rockBlock usage

bool dataTransmission(){

  /*
  This function is responsible for the transmission of data with the rockBLOCK. 
  This function will continously try to send data until a timelimit, specified in
  NUMBER_OF_TRANMISSION_ATTEMPTS 

  returns true/false -> success/failure
  */

  for (int i = 1; i < NUMBER_OF_TRANSMISSION_ATTEMPTS; i++){

    Serial.println("WAITING 50 SECONDS FOR CAPACITOR TO CHARGE");
    delay(50000); // 1000 milliseconds => 1 second * 50 => 50 seconds

    Serial.print("SENDINDG DATA: ATTEMPT (");
    Serial.print(i);
    Serial.print("/");
    Serial.print(NUMBER_OF_TRANSMISSION_ATTEMPTS);
    Serial.println(")");

    Serial.println("Before modem.sendSBDBinary()");
    int isbd_status_message = modem.sendSBDBinary(data_pointer, DATA_ARRAY_SIZE);
    Serial.println("After modem.sendSBDBinary()");
    
    if (isbd_status_message == ISBD_SUCCESS){
      Serial.println("ISBD STATUS: SUCCESS");
      return true; // success
    }
    else{
      Serial.print("ISBD STATUS: FAILURE - MESSAGE ");
      Serial.println(isbd_status_message); 
      
      Serial.println("SENDING DATA FAILED, ATTEMPTING AGAIN IN 30 SECONDS (AFTER ROCKBLOCK RECHARGED)");
      delay(30000); // 1000 milliseconds => 1 second * 30 => 30 seconds
    }
  }

  // After the NUMBER_OF_TRANMISSION_ATTEMPS is surpassed, return failure
  return false;
}

//////////////////////////////////////////////////////////////////////////////
// NOTE!!!!!!!
// Both functions below are REQUIRED in the code in order for the library to be utilized, even if they aren't used directly.

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
