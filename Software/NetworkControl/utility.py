# Common Core Libraries
import sys
import time

# Third Party Imports
import pandas as pd
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Local Imports
import classes as clss
import global_variables as gv

#----------------------------------------------------------------
# Functions 

def sort_and_clean_df(df, index="time_id", asc_order = False):

    try:
        df = df.set_index(index)
    except:
        pass
    df = df.sort_values(by=index, ascending=asc_order)
    df = df.loc[~df.index.duplicated(keep="first")]

    return df

def update_mysql_database(fetch_type, number_of_emails_per_station):

    # Getting the latest email data frame
    email_client = clss.email_client.EmailClient()
    email_client.fetch_uids(fetch_type, number_of_emails_per_station)
    
    if email_client.email_info == {}: # No fetched UIDS
        return None # Leave the function

    email_client.fetch_emails_text()
    email_client.parse_emails_text()

    # Testing DataFrame Handler
    dataframe_handler = clss.DataFrameHandler(email_client.email_info)

    # MySQL Integration
    mysql_client = clss.mysql_client.MySQLClient()
    mysql_client.fetch_data(limit="None")

    # Testing DataFrame Handler
    dataframe_handler.trim_to_only_new_entries(mysql_client.mysql_table_df)
    mysql_client.add_entries(dataframe_handler.all_emails_df)

    mysql_client.close()

    return None

def generate_table_file():

    # Fetching the last values of each table
    mysql_client = clss.mysql_client.MySQLClient()
    mysql_client.fetch_data(limit=1)

    # Creating new dataframe with these values and creating a CSV file
    datafile_generator = clss.DatafileGenerator()
    datafile_generator.generate_latest_data_table(mysql_client.mysql_table_df)

    return None

def generate_plot_file(size):

    # Fetching the last 30 values of each table
    mysql_client = clss.mysql_client.MySQLClient()
    mysql_client.fetch_data(limit=size)

    # Creating JPGs -> PDF plots of each station 
    datafile_generator = clss.DatafileGenerator()
    datafile_generator.generate_plots(mysql_client.mysql_table_df)

    return None

def generate_markers_file():

    # Fetching the last 30 values of each table
    mysql_client = clss.mysql_client.MySQLClient()
    mysql_client.fetch_data(limit=1)

    # Creating JPGs -> PDF plots of each station 
    datafile_generator = clss.DatafileGenerator()
    datafile_generator.generate_station_markers(mysql_client.mysql_table_df)

    return None

def upload_all_data_files():

    data_uploader = clss.DataUploader()
    data_uploader.upload_all_data_files()
    
    return None

#---------------------------------------------------------------
# Decorators

def email_failure_reporting(func):

    def send_failure_email():

        # Email Information
        subject = "ERROR OCCURED IN EMAIL MONITORING"
        text = """\
        Error within the Network Control System
        Please restart the code after checking for the error.

        Error Message: 
        {0}
        -Ed
        """.format(str(sys.exc_info()))

        # Setup up SSL
        port = 465 # For SSL
        context = ssl.create_default_context()

        # Constructing message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = gv.RASPBERRY_PI_EMAIL
        message["To"] = gv.PERSONAL_EMAIL

        text_part = MIMEText(text, "plain")
        message.attach(text_part)

        # Sending the email
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context = context) as server:
            server.login(gv.RASPBERRY_PI_EMAIL, gv.RASPBERRY_PI_EMAIL_PASSWORD)

            server.sendmail(gv.RASPBERRY_PI_EMAIL, 
                            gv.PERSONAL_EMAIL, 
                            message.as_string())

        return None

    def wrapper():

        # 
        attempt_counter = 0
        
        while True:
            try:
                # Executing all main routines
                func()
                attempt_counter = 0
            
            except:

                # Only letting re-run for 5 attempts
                attempt_counter += 1

                if attempt_counter >= 5:
                    raise RuntimeError("Too many attempts to run main.py")

                # Reporting failure
                print("SENDING ERROR EMAIL")
                send_failure_email()
                print("SLEEPING FOR 1 MINUTE FOR RESTARTING")
                time.sleep(1 * 60)

    return wrapper