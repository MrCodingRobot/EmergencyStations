# Common Core Libraries
import time
import sys
import datetime
import os

# Local Imports
import error_email
import email_monitor
import functions

TROUBLESHOOTING = True

#---------------------------------------------------------------------------
# This is the main file

print("Current CWD: " + os.getcwd())

# Apending the file path (main.py) to PATH
if sys.platform == "win32":
    print("Appending __file__ path to win32 OS")
    file_path = '\\'.join(os.path.abspath(__file__).split('\\')[:-1])
    
elif sys.platform == "linux":
    print("Appending __file__ path to linux OS")
    file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1])

print("File Path: " + file_path)
sys.path.insert(0, file_path)


"""
To Do:
    Get Google Maps Working (Parsing Error) 
    Make Code Compatible to Linux OS
"""

"""
This is to ensure that some relative file imports work
when running the main.py file from a different file.
"""

# Google Drive Setup
# Should only ever run once
functions.google_drive_setup()

if TROUBLESHOOTING is False:

    while True:
        try: 
            # Informing via email that email monitoring is happening
            subject = "STARTING EMAIL MONITORING"
            text = "Starting email monitoring at {0}".format(datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S CDT"))
            error_email.main(subject, text)

            email_monitor.main()

        except KeyboardInterrupt: 
            print("CTRL-C DETECTED, EXIT PROGRAM")
            break

        except:
            print("ERROR OCCURED DURING EMAIL MONITOR")
            print("INFORMING ERROR VIA EMAIL")

            string_error = str(sys.exc_info())

            # Informing via email that an error has occured
            subject = "ERROR OCCURED IN EMAIL MONITORING"
            text = """\
            Error within the Network Control System
            Please restart the code after checking for the error.

            Error Message: 
            {0}
            -Ed
            """.format(string_error)

            error_email.main(subject, text)
            print("SLEEPING FOR A MINUTE AND THEN RESTARTING")
            time.sleep(60)

else: # Troubleshooting true
    email_monitor.main()