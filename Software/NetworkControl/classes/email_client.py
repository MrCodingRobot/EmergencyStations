# Library Imports
import os
import sys

# Third-Party Imports
import imapclient
import pyzmail
import pandas as pd
import datetime
import pytz

# Local Imports
ROOT_DIR = os.path.abspath("../")
sys.path.append(ROOT_DIR)

import global_variables as gv
import utility as util

#-------------------------------------------------------------
# Class 

class EmailClient():

    """
    The EmailClient class/module is responsible of fetching, 
    parsing, and passing on the information within the emails 
    recieved from the stations.

    Firstly, the UIDs are fetched depending on the type of search
    is being conducted ("New", "Last" and "All"). Then the actual email
    text has to be obtained with recently aquired UIDs. Afterwards,
    the email's text has to be processed/parsed to retrieve the 
    information of the stations (weight, location, and status)

    Then this processed data is passed to the MySQLClient to 
    update the MySQL database containing all the information 
    of the stations.
    """

    def __init__(self):

        # Initializing the primary attributes of the class

        self.imap_client = self.imap_client_setup()
        self.email_info = {}

        """
        email_info structure
            {"station_email": 
                {uid: {
                    "text": str,
                    "dataframe": {
                        "time_id": (datetime, ...),
                        "sensor_1": (int, ...),
                        "sensor_2": (int, ...),
                        "sensor_3": (int, ...),
                        "reference": (int, ...),
                        "weight_lbs": (int, ...),
                        "longitude": (float, ...),
                        "latitude": (float, ...),
                        "timezone": (str, ...)
                        }
                    }
                }
            }

        """

        return None

    def imap_client_setup(self):

        """
        This function helps the setup of the imap client.
        """

        imap_client = imapclient.IMAPClient(gv.IMAP_SERVER, ssl = True)
        imap_client.login(gv.TRINITY_EMAIL, gv.TRINITY_EMAIL_PASSWORD)

        return imap_client

    def is_there_new_emails(self):

        """
        Checking for new emails
        """
        new_emails_quantity = 0
        for water_station in gv.STATION_INFO:
            self.email_uids[water_station["email"]] = self.fetch_uids(water_station["email"], "New")
            new_emails_quantity += len(self.email_uids[water_station["email"]])
            
        if new_emails_quantity > 0:
            return True

        return False

    def fetch_uids(self, fetch_type = "Last", last_quantity = 1):

        """
        Before getting the email's juicy information, we have to get the email's 
        UIDs. We have get "All" of the email's UIDs, the "New" ones, or just the 
        "Last" ones. The "Last" fetch type has the ability of increasing the fetch 
        range of the last email's UIDs with the last_quantity attribute.
        """

        for water_station in gv.STATION_INFO:

            # Fetching emails based on selected category
            if fetch_type == "All":
                self.imap_client.select_folder('[Gmail]/All Mail')
                uids = self.imap_client.search(['FROM', water_station["email"]])

            elif fetch_type == "New":
                self.imap_client.select_folder("INBOX")
                uids = self.imap_client.search(["FROM", water_station["email"]])

            elif fetch_type == "Last":
                self.imap_client.select_folder('[Gmail]/All Mail')
                uids = self.imap_client.search(['FROM', water_station["email"]])[-1 * last_quantity:]

            # uids need to be in a list
            if not isinstance(uids, list) and uids:
                uids = [uids]

            print(uids)

            if len(uids) != 0: # Only creating entries for emails that have uids
                self.email_info[water_station["email"]] = dict(zip(uids,[{} for i in range(len(uids))]))

        return self.email_info

    def fetch_emails_text(self):

        """
        Now that we have the emails UIDs, now we can obtain the text information
        within the emails. 
        """

        for station_email, uid_content in self.email_info.items():

            for uid in uid_content.keys():

                email_text = None

                # Getting the raw text information of the email
                raw_message = self.imap_client.fetch(uid, ['BODY[]'])

                # Processing the text information to make it easier to read
                message = pyzmail.PyzMessage.factory(raw_message[uid][b'BODY[]'])

                if message.html_part != None:
                    email_text = message.html_part.get_payload().decode(message.html_part.charset)

                if message.text_part != None:
                    email_text = message.text_part.get_payload().decode(message.text_part.charset)

                # Appending the text to the self.email_info attribute to keep track of info
                self.email_info[station_email][uid]["text"] = email_text

        return self.email_info

    def parse_emails_text(self):

        """
        This function then retrieves the information found within the text
        of the email.
        """

        if self.email_info == {}:
            raise RuntimeError("Please fetch emails before parsing emails")

        for station_email, uid_content in self.email_info.items():

            #print("################################################")
            #print(station_email)

            for uid, email_content in uid_content.items():

                lines = email_content["text"].split("\n")

                # Obtaining essential information (time and hex data) from the email's text

                original_time_id = lines[3].split(" ")[2] + lines[3].split(" ")[3].replace("\r","") # UTC timeline
                
                if lines[8].find("Data") is not -1:
                    hex_data = lines[8].split(" ")[1].replace("\r","") # for all 12 hours
                elif lines[7].find("Data") is not -1:
                    hex_data = lines[7].split(" ")[1].replace("\r","") # for all 12 hours

                # Generating multiple entries for the individual email

                time_values = self.generate_time_id_set(original_time_id) # [time_id1, time_id2, ...]
                
                try:
                    # Place into a single "data" variable to easily print and to troubleshoot output
                    data = self.generate_data_set(hex_data) # [s1, ...],[s2, ...],[s3, ...],[ref, ...],[weight, ...] 
                except RuntimeError:
                    continue
                
                sensor1, sensor2, sensor3, ref, weight = data

                # Save data to original dictionary

                data = {"time_id": time_values,
                        "sensor_1": sensor1,
                        "sensor_2": sensor2,
                        "sensor_3": sensor3,
                        "reference": ref,
                        "weight_lbs": weight,
                        "latitude": [lines[4].split(" ")[2].replace("\r", "") for i in range(8)],
                        "longitude": [lines[5].split(" ")[2].replace("\r", "") for i in range(8)],
                        "timezone": ["CST" for i in range(8)]}

                # Creating dataframe for UID
                
                df = pd.DataFrame(data)
                df = util.sort_and_clean_df(df)

                self.email_info[station_email][uid]["dataframe"] = df

                # Printing information

                #print("UID: {}".format(uid))
                #print(df)
                #print("Email Information: {}".format(email_content))

        return self.email_info

    def generate_time_id_set(self, original_time_id):

        # 90 minutes apart for Phase 1 stations, 8 total entries
        
        # Time String Formatting
        original_time_id = original_time_id.replace("T", " ", 1).replace("Z", " ")

        # Timezone Unaware -> Timezone Aware
        utc_datetime = datetime.datetime.strptime(original_time_id, "%Y-%m-%d %H:%M:%S %Z")
        #utc_datetime = utc_datetime.replace(tzinfo = pytz.UTC)

        # Changing from UTC to CDT/CST Timezone
        #cst_timezone = pytz.timezone("US/Central")
        #cst_datetime = utc_datetime.astimezone(cst_timezone)
        cst_datetime = utc_datetime - datetime.timedelta(hours=6)

        # Creating list of time values
        time_values = []

        for i in range(8):
            #time_values.append(cst_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            time_values.append(cst_datetime)
            cst_datetime = cst_datetime - datetime.timedelta(minutes=90)

        return time_values

    def generate_data_set(self, hex_data):

        # 8 total entries & output = (sensor1,sensor2,sensor3,ref,weight)

        if hex_data == None: # Corrupted Data Transmission
            raise RuntimeError("CORRUPTED DATA TRANSMISSION")

        text_data = bytearray.fromhex(hex_data) 

        data = [[],[],[],[],[]]

        for i in range(8): # Obtaining information from hex data
            data[0].append(text_data[i*5 + 2]) # sensor1
            data[1].append(text_data[i*5 + 3]) # sensor2
            data[2].append(text_data[i*5 + 4]) # sensor3
            data[3].append(text_data[i*5 + 5]) # ref
            data[4].append(text_data[i*5 + 6]) # weight_lbs   

        for i in range(5): # Reversing the order of the data
            data[i].reverse()

        return data

#---------------------------------------------------------------
# Running Code

if __name__ == "__main__":

    """
    This section is for testing purpose regarding this class
    """

    # Testing __init__
    email_client = EmailClient()

    # Testing if .is_there_new_emails function
    #print(email_client.is_there_new_emails())

    # Testing fetching emails and their information
    email_client.fetch_uids("Last", 10)
    #email_client.fetch_uids("All")

    email_client.fetch_emails_text()
    email_client.parse_emails_text()




