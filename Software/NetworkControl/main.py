# Common Core Libraries
import time
import sys
import datetime
import os

# Local Imports
import utility as util
import classes as clss

#--------------------------------------------------------------------
# Main Functions

@util.email_failure_reporting
def main():

    # Reporting time when routines are executed
    print("CHECKING EMAILS AT " + str(datetime.datetime.now()))
    
    # First update mysql database
    print("UPDATING MYSQL DATABASE")
    util.update_mysql_database("New", 1)
    util.update_mysql_database("Last", 2)

    # Generate all output files
    print("GENERATING OUTPUT FILES")
    util.generate_table_file()
    util.generate_plot_file(30)
    util.generate_markers_file()

    # Upload data to server
    print("UPLOADING DATA TO SERVER")
    util.upload_all_data_files()

    # Sleeping for 10 minutes
    print("SLEEPING FOR 10 minutes")
    time.sleep(10 * 60)

    return None

#--------------------------------------------------------------------
# Main Code

main()

