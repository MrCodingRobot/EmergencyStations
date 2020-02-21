# Author: Eduardo Davalos Anaya
# Last Edited: 6/4/2019

# Common Core Libraries
import time
import csv
import datetime
import time
import ftplib
import logging
import logging.handlers

# Third-Party Libraries
import imapclient
import pyzmail

# Local Imports
import global_variables
import functions
import classes

#---------------------------------------------------------------------------------------------------
# Task: Retrieve last email and monitor upcoming emails, then update the website

def main():
    
    # Initialization
    print("\n\n")
    print(". . . EMAIL BOT STARTED. PRESS CTRL-C TO QUIT . . .")
    print("\n\n")

    # Logging Setup
    logger = functions.logging_setup("water_station_logger")
    logger.critical("Initiating Email Bot")

    # Water Station Instances Initialization

    water_stations_list = []

    for station_info in global_variables.STATION_INFO:

        if station_info[1] == '1': # Phase One Stations
            water_stations_list.append(classes.PhaseOneStation(station_info))
        elif station_info[1] == '2': # Phase Two Stations
            water_stations_list.append(classes.PhaseTwoStation(station_info))

    #---------------------------------------------------------------------------------------------------
    # Obtaining the latest email information

    imap_client = functions.imap_client_setup()

    functions.print_header("DETERMING LATEST EMAIL")
    logger.info("############################## DETERMING LATEST EMAIL ###############################")

    for water_station in water_stations_list:

        # Email Fetching and Parsing
        water_station.email_to_upload_data(imap_client)
        logger.info("Station {0} Email Data: {1}".format(water_station.number_label, water_station.data))

    functions.create_upload_and_save_files(water_stations_list, logger)
    imap_client.logout()

    #--------------------------------------------------------------------------------------------------
    # Monitoring for new emails

    functions.print_header("MONITORING UPCOMING EMAILS")
    logger.info("############################### MONITORING UPCOMING EMAILS ############################")

    while True:

        print("CHECKING FOR NEW EMAIL AT " + str(datetime.datetime.now()))
        imap_client = functions.imap_client_setup()
        new_email_flag = False

        for water_station in water_stations_list:

            if water_station.new_email(imap_client) is True:

                new_email_flag = True
        
                print("NEW EMAIL DETECTED")
                logger.info("New email detected: Station {}".format(water_station.number_label))
                water_station.remove_new_email_from_inbox(imap_client)

                # Email Fetching and Parsing
                water_station.email_to_upload_data(imap_client)
                logger.info("Station {0} Email Data: {1}".format(water_station.number_label, water_station.data))

        if new_email_flag == True:

            functions.create_upload_and_save_files(water_stations_list, logger)

        print("SLEEPING")
        imap_client.logout()
        time.sleep(global_variables.MONITORING_DELAY)

# Purely for troubleshooting
#main()




    

    
