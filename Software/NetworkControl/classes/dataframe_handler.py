# Library Imports 
import os
import sys

# Third-Party Imports
import pandas as pd

# Local Imports
ROOT_DIR = os.path.abspath("../")
sys.path.append(ROOT_DIR)

import utility as util

#--------------------------------------------------------------------------
# Class

class DataFrameHandler():

    """
    This module, DataFrameHandler, is a small class that grabs the emails (accounts) dataframes,
    with the possibility of multiple emails per emails (accounts) and creates a single dataframe
    for each email account. Additionally, it removes duplicates and cleans the dataframe. Then
    the DataFrameHandler passes on this clean simple dataframe to the MySQLClient for upload. 
    """

    def __init__(self, email_info):

        # Creating some of the primary class attributes

        self.email_info = email_info
        self.all_emails_df = {}
        self.generate_all_emails_df()

        """
        all_emails structure
            {"station_email": <dataframe object>}

        """

        return None

    def generate_all_emails_df(self):

        # Generating all_emails_df, it being the combined emails dataframe

        for station_email, uids_content in self.email_info.items():

            uid_keys = list(uids_content.keys()) 
            uid_keys.reverse() # got to reverse since last uids are the latest info

            df = self.email_info[station_email][uid_keys[0]]["dataframe"]

            # Appending emails into a single df
            for i in range(1,len(uid_keys)):
                df = df.append(uids_content[uid_keys[i]]["dataframe"])

            # Cleaning and sorting dataframe
            df = util.sort_and_clean_df(df)

            self.all_emails_df[station_email] = df

        return None

    def trim_to_only_new_entries(self, mysql_table_df):

        self.mysql_table_df = mysql_table_df

        #print("Pre-Trimming: {}".format(self.all_emails_df['300234067638620@rockblock.rock7.com'].shape))
        #print(self.all_emails_df['300234067638620@rockblock.rock7.com'])

        for station_email, mysql_df in self.mysql_table_df.items():

            # Find what is shared between the mysql df and the emails df
            shared_df_index = mysql_df.index.intersection(self.all_emails_df[station_email].index)
            shared_df = self.all_emails_df[station_email].loc[shared_df_index]

            if shared_df.empty is True: # if nothing is shared, then emails df is ready
                print("NOTHING SHARED")
            else: # else, remove the shared from the emails df to upload to mysql server
                unique_df_index = shared_df.index.symmetric_difference(self.all_emails_df[station_email].index)
                unique_df = self.all_emails_df[station_email].loc[unique_df_index]
                unique_df = util.sort_and_clean_df(unique_df)
                self.all_emails_df[station_email] = unique_df

        #print("Post-Trimming: {}".format(self.all_emails_df['300234067638620@rockblock.rock7.com'].shape))
        #print(self.all_emails_df['300234067638620@rockblock.rock7.com'])

        return None

#---------------------------------------------------------------------------
# Running Code

if __name__ == "__main__":

    """
    This section is for testing purposes regarding the DataFrameHandler class
    """

    import email_client
    import mysql_client

    # Getting the latest email data frame
    email_client = email_client.EmailClient()
    email_client.fetch_uids("Last", 35)
    email_client.fetch_emails_text()
    email_client.parse_emails_text()

    # Testing DataFrame Handler
    dataframe_handler = DataFrameHandler(email_client.email_info)

    # MySQL Integration
    mysql_client = mysql_client.MySQLClient()
    mysql_client.fetch_data(limit="None")

    # Testing DataFrame Handler
    dataframe_handler.trim_to_only_new_entries(mysql_client.mysql_table_df)

    mysql_client.close()