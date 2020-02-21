# Library Imports
import os
import sys

# Third-Party Library Imports
import mysql.connector
import pandas as pd
import sqlalchemy

# Local Imports
ROOT_DIR = os.path.abspath("../")
sys.path.append(ROOT_DIR)

import global_variables as gv
import utility as util

#---------------------------------------------------------------------
# Class

class MySQLClient():

    def __init__(self):

        """
        Initializes the connection to the MySQL server that is hosted by southtexashrc.com
        """

        self.cnx = mysql.connector.connect(user=gv.MYSQL_INFO["user"],
                                           password=gv.MYSQL_INFO["password"],
                                           host=gv.MYSQL_INFO["host"],
                                           database=gv.MYSQL_INFO["database"])
        self.cursor = self.cnx.cursor()
        self.mysql_table_df = {}

        """
        self.mysql_table_df structure
            {"station_email": df, ...}
        """

        return None

    def add_entries(self, all_emails_df):

        """
        This function is for adding new entries to the database in this format
        """

        engine = sqlalchemy.create_engine("mysql://southti6_eduardo:davalos97@southtexashrc.com/southti6_StationsWeightLevel")
        con = engine.connect()

        for station_email, df in all_emails_df.items():
            station_table = gv.EMAIL2TABLE[station_email]
            
            if df.empty is True: # if the dataframe is empty, skip it
                print("TABLE: {} - DF: Empty".format(station_table))
                continue

            print("TABLE: {}\nDF: {}".format(station_table, df))
            df.to_sql(con=con, name=station_table, if_exists="append")

        con.close()

        self.remove_duplicates()
        self.order_by_time()

        return None

    def remove_duplicates(self):

        for station in gv.STATION_INFO:

            command = ("ALTER TABLE {} ADD UNIQUE (time_id)".format(station["table"]))
            self.cursor.execute(command)

        return None

    def order_by_time(self):

        for station in gv.STATION_INFO:

            command = ("ALTER TABLE {} ORDER BY time_id DESC".format(station["table"]))
            self.cursor.execute(command)

        return None

    def fetch_data(self, limit = gv.AUTOPLOT_VALUE_SIZE_LIMIT):

        for station in gv.STATION_INFO:

            if limit == "None":
                command = ("SELECT * FROM {}".format(station["table"]))
            else:
                command = ("SELECT * FROM {} LIMIT {}".format(station["table"], limit))
            
            self.cursor.execute(command)

            table_rows = self.cursor.fetchall()
            df = pd.DataFrame(table_rows, columns=self.cursor.column_names)
            df = util.sort_and_clean_df(df)

            self.mysql_table_df[station["email"]] = df

        return None

    def close(self):
        # Closing the session
        self.cnx.commit()
        self.cursor.close()
        self.cnx.close()

        return None

#----------------------------------------------------------------------------------------
# Running Code

if __name__ == "__main__":
    
    """
    Testing if the class is working properly
    """

    import dataframe_handler
    import email_client
    
    mysql_client = MySQLClient()

    # Fetch Check
    mysql_client.fetch_data(limit = "None")
    #print(mysql_client.mysql_table_df)

    # Removing duplicates and reordering
    #mysql_client.remove_duplicates()
    #mysql_client.order_by_time()


    # Getting the latest email data frame
    email_client = email_client.EmailClient()
    email_client.fetch_uids("Last", 35)
    email_client.fetch_emails_text()
    email_client.parse_emails_text()

    # Testing DataFrame Handler
    dataframe_handler = dataframe_handler.DataFrameHandler(email_client.email_info)

    # MySQL Integration
    mysql_client = MySQLClient()
    mysql_client.fetch_data(limit="None")

    # Testing DataFrame Handler
    dataframe_handler.trim_to_only_new_entries(mysql_client.mysql_table_df)
    mysql_client.add_entries(dataframe_handler.all_emails_df)
    
    mysql_client.close()
    