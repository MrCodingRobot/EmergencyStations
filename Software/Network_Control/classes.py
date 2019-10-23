# Common Core Libraries
import datetime
import pandas as pd
import pytz
import xlrd

# Third-Party Libraries
import imapclient
import pyzmail

import global_variables
import functions

#---------------------------------------------------------------------------------
# Classes

class WaterStation(object):

    """
    This is the general class for water stations. This contains methods and 
    other variables that are shared between the children classes: PhaseOneStation
    and PhaseTwoStations.
    """

    def __init__(self, station_info):

        """
        This is the initilization function for the class. This includes the
        initialization of universal variables.
        """

        self.uploaded_data = ['','','','','','','','']
        self.number_label = station_info[0]
        self.email = station_info[2]
        self.parsing_version = station_info[3]
        self.imei = station_info[2].split("@")[0]
        self.email_body = None
        self.data = None
        self.hex_data = None
        self.clock = {'year': 0, 'month': 0, 'day': 0, 'hour': 0, 'minute': 0, 'second': 0}

        return None

    # Email Processing

    def get_uids(self, imap_client, type = "New"):

        """
        This function returns a list of new uids from the water station's email.
        """

        if type == "All":
            imap_client.select_folder('[Gmail]/All Mail')
            uids = imap_client.search(['FROM', self.email])
        
        elif type == "New":
            imap_client.select_folder('INBOX')
            uids = imap_client.search(['FROM', self.email])

        return uids

    def fetch_email_body(self, imap_client, uid):

        """
        This function obtains the email body of any specific uid
        """

        raw_message = imap_client.fetch(uid, ['BODY[]'])
        message = pyzmail.PyzMessage.factory(raw_message[uid][b'BODY[]'])

        if message.html_part != None:
            email_body = message.html_part.get_payload().decode(message.html_part.charset)

        if message.text_part != None:
            email_body = message.text_part.get_payload().decode(message.text_part.charset)

        return email_body

    def email_line_breaking(self, email_body):

        """
        This function reads and breaks down the information contents of the email.
        An example email can be found the global_variables module.
        """

        data = {'hex_data': None, 'latitude': None, 'longitude': None, 'cep': None,
                'transmit_time': None}

        if email_body != None:

            lines = email_body.split('\n')

            #print(lines)

            for line in lines:
            
                if line.startswith('Data'):
                    if line.startswith('No Data'):
                        print("EMAIL WITH NO DATA!")
                        data['hex_data'] = None
                        continue

                    data['hex_data'] = line[6:-1]
            
                elif line.startswith('Iridium Latitude'):
                    data['latitude'] = line[18:-1]
                    self.latitude = data['latitude']
            
                elif line.startswith('Iridium Longitude'):
                    data['longitude'] = line[19:-1]
                    self.longitude = data['longitude']

                elif line.startswith('Iridium CEP'):
                    data['cep'] = line[13:-1]

                elif line.startswith('Transmit Time:'):
                    data['transmit_time'] = line[15:-1]
            
        return data

    # Email Monitoring Status

    def new_email(self, imap_client):

        """
        This helper function simply informs if a new email has been recieved.
        """

        imap_client.select_folder('INBOX')
        uids = imap_client.search(['FROM', self.email])

        print("uids: ", uids)

        if len(uids) > 0:
            return True
        
        return False

    def remove_new_email_from_inbox(self, imap_client):

        """
        To ensure that we don't read the same email, we remove the 
        already-read emails from the GMAIL INBOX.
        """


        # Not certain if "deleting" the UIDS is the way to.
        # Perhaps marking them as "read" would be better.

        imap_client.select_folder('INBOX')
        uids = imap_client.search(['FROM', self.email])

        imap_client.delete_messages(uids)

        return None

    # Parsing

    def universal_parsing_hex_data(self, data):

        """
        This function is for certain parsing version for the PhaseOneStation
        while this is fully applicable to PhaseTwoStation. This function is involved
        with how the transmitted string is interpreted into useful data.
        """

        #print("Universal Parsing")

        if data['hex_data'] == None:

            parse_data = self.hex_data_none_case()
        
        else:

            #print("Hex Data Found")
            text_data = bytearray.fromhex(data['hex_data'])
            parse_data = {}

            parse_data['transmitted_number_label'] = text_data[0]
            parse_data['alarm'] = text_data[1]


            parse_data['current_weight'] = float(text_data[45])
            parse_data['current_amps'] = (float(text_data[46])/100) # 100
            parse_data['current_volt'] = (float(text_data[47])/10)  # 10

            parse_data['jugs'] = int(round((parse_data['current_weight'] / global_variables.JUG_WEIGHT), 0))
            parse_data['current'] = parse_data['current_amps']
            parse_data['volt'] = parse_data['current_volt']

            if isinstance(self, PhaseTwoStation):
                
                parse_data['current_index'] = ((text_data[44] * 3) - 1)
                
                # Checking if present values are different from current index
                # values. They should be the same.
                parse_data['current_index_weight'] = float(text_data[parse_data['current_index']])
                parse_data['current_index_amps'] = (float(text_data[parse_data['current_index'] + 1])/100) # 100
                parse_data['current_index_volt'] = (float(text_data[parse_data['current_index'] + 2])/10) # 10
                
                if ( parse_data['current_index_weight'] != parse_data['current_weight'] or \
                     parse_data['current_index_amps'] != parse_data['current_amps'] or \
                     parse_data['current_index_volt'] != parse_data['current_volt'] ):
                       
                   print("PHASE TWO PRESENT VALUES DO NOT MATCH CURRENT INDEX VALUES")
                   print("OVERWRITING PRESENT VALUES WITH CURRENT INDEX VALUES")
                   
                   parse_data['current_weight'] = parse_data['current_index_weight']
                   parse_data['current_amps'] = parse_data['current_index_amps']
                   parse_data['current_volt'] = parse_data['current_index_volt']
                   
                # Allocating the previous index value
                index = text_data[44] - 1
                
                if index <= 0:
                    index = 14
                
                parse_data['previous_index'] = index * 3 - 1       
                
                parse_data['old_weight'] = float(text_data[parse_data['previous_index']])
                parse_data['old_amps'] = (float(text_data[parse_data['previous_index'] + 1])/100) # 100
                parse_data['old_volt'] = (float(text_data[parse_data['previous_index'] + 2])/10) # 10

                parse_data['average_weight'] = (parse_data['current_weight'] + parse_data['old_weight'])/2
                parse_data['average_amps'] = (parse_data['current_amps'] + parse_data['old_amps'])/2
                parse_data['average_volt'] = (parse_data['current_volt'] + parse_data['old_volt'])/2

                parse_data['jugs'] = int(round((parse_data['average_weight'] / global_variables.JUG_WEIGHT), 0))
                parse_data['current'] = parse_data['average_amps']
                parse_data['volt'] = parse_data['average_volt']

            elif isinstance(self, PhaseOneStation):

                parse_data['current'] = global_variables.NOT_IMPLEMENTED_STRING
                parse_data['volt'] = global_variables.NOT_IMPLEMENTED_STRING

        
        print("***********************************************************")
        print("Station {0} (Listed by Email)".format(self.number_label))

        for key in parse_data.keys():
            print(key + ": {0}".format(parse_data[key]))

        return parse_data

    def complete_data_parsing_and_collection(self, data):

        """
        This function deals with the complete recovery of the water stations'
        data pertaining. This data includes periodatic data from the water 
        stations sensors and calculated weights.
        """

        # 50 minutes

        if data['hex_data'] == None:
            print("COMPLETE DATA COLLECTION ATTEMPTED WITH HEX_DATA BEING NONE")
            return None

        text_data = bytearray.fromhex(data['hex_data'])

        #print("Text Data: {}".format(text_data))

        # Time String Formatting
        trimmed_time = data['transmit_time'].replace("T", " ", 1).replace("Z", "")
        local_format = "%Y-%m-%d %H:%M:%S %Z"

        # Timezone Unaware -> Timezone Aware
        utc_datetime_object = datetime.datetime.strptime(trimmed_time, local_format)
        utc_datetime_object = utc_datetime_object.replace(tzinfo = pytz.UTC)

        # Changing from UTC to CDT Timezone
        central = pytz.timezone("US/Central")
        central_datetime_object = utc_datetime_object.astimezone(central)

        #---------------------------------------------------------------------
        # Pairing Data from original data

        collected_data = []

        if isinstance(self, PhaseOneStation) is True:

            j = 2

            while j + 5 <= len(text_data) - 6:
                collected_data.append(['time', text_data[j], text_data[j + 1], text_data[j + 2],
                                      text_data[j + 3], text_data[j + 4]])
                j += 5

        elif isinstance(self, PhaseTwoStation) is True:
            
            j = 2

            while j + 3 <= len(text_data) - 4:
                collected_data.append(['time', text_data[j], text_data[j + 1], text_data[j + 2]])
                j += 3

        #print("Collected Data")
        #print(collected_data)
        collected_data.reverse()

        #---------------------------------------------------------------------
        # Sorting Data based on Time

        sorted_collected_data = []
        new_datetime_central = central_datetime_object

        if isinstance(self, PhaseOneStation):

            for index in range(len(collected_data)):
                #print("Index: " + str(index) + " Length: " + str(len(collected_data)))

                time = new_datetime_central.strftime(local_format)
                collected_data[index][0] = time

                new_datetime_central = new_datetime_central - datetime.timedelta(minutes = 90)

            sorted_collected_data = collected_data

        elif isinstance(self, PhaseTwoStation):

            index = text_data[44]
            index_pair = int( (index - 2) / 3)
            _index_pair = index_pair
            flag = False

            #print("Index: " + str(index))

            while True:
                #print("Index Pair: " + str(index_pair) + " Length: " + str(len(collected_data)))

                if index_pair >= len(collected_data):
                    break
            
                time = new_datetime_central.strftime(local_format)
                collected_data[index_pair][0] = time

                sorted_collected_data.append(collected_data[index_pair])

                index_pair += 1
                if index_pair >= len(collected_data) and flag is False and _index_pair != 0:
                    index_pair = 0
                    flag = True

                new_datetime_central = new_datetime_central - datetime.timedelta(minutes = 50)

                if index_pair == _index_pair and flag is True:
                    break

        #print("Sorted Collected Data")
        #print(sorted_collected_data)

        if isinstance(self, PhaseOneStation):
            df = pd.DataFrame(sorted_collected_data, columns = ['Time', 'Sensor 1','Sensor 2','Sensor 3', 'Reference','Weight'])

        elif isinstance(self, PhaseTwoStation):
            df = pd.DataFrame(sorted_collected_data, columns = ['Time', 'Weight','Current','Voltage'])

        df = df.sort_values(by='Time')
        df = df.set_index('Time')
        df = df.loc[~df.index.duplicated(keep='first')]
        #print("df")
        #print(df)
        
        #-----------------------------------------------------------------------
        # Placing information into Excel

        sheet_name_format = "Station " + str(self.number_label) + " (" + str(self.imei) + ")"
        xls = xlrd.open_workbook(global_variables.CSV_FORMATTER_FILE_PATH, on_demand=True)
        sheet_names = xls.sheet_names()

        frames = {}

        # Reading all sheets and storing DataFrames into a dictionary
        for current_sheet_name in sheet_names:
            frames[current_sheet_name] = pd.read_excel(global_variables.CSV_FORMATTER_FILE_PATH,
                                                       sheet_name = current_sheet_name)
            
            frames[current_sheet_name] = frames[current_sheet_name].sort_values(by="Time")
            frames[current_sheet_name] = frames[current_sheet_name].set_index("Time")


        # If current station info is already in excel, then append it
        if sheet_name_format in sheet_names:

            old_df = frames[sheet_name_format]
            #print("old_df")
            #print(old_df)

            combining_frames = [df, old_df]
            result = pd.concat(combining_frames)

        # Else just make the entire data in that sheet the new data
        else:
            result = df

        #print("result")
        #print(result)

        result = result.sort_values(by='Time')
        #result = result.set_index('Time')
        result = result.loc[~result.index.duplicated(keep='first')]

        #print("New Result")
        #print(result)

        # Storing the new dataframe into the dataframe dictionary
        frames[sheet_name_format] = result

        #print("frames")
        #print(frames)

        # Write all of the dataframes back into the excel

        with pd.ExcelWriter(global_variables.CSV_FORMATTER_FILE_PATH) as writer:

            for current_sheet_name in frames.keys():

                if frames[current_sheet_name].empty == True:
                    # Empty Sheet
                    continue

                frames[current_sheet_name].to_excel(writer, sheet_name=current_sheet_name)

        # Autoplotting graphs
        functions.autoplot_excel()

        return None

    def hex_data_none_case(self):

        """
        This function deals with the case in which the email contains no
        hex information. This is simply a helper function.
        """
        
        #print("Hex Data: No Data Case")
        
        parse_data = {}
        parse_data['weight'] = "No Data"
        parse_data['jugs'] = "No Data"
        parse_data['current'] = "No Data"
        parse_data['volt'] = "No Data"
        parse_data['data'] = "No Data"
        parse_data['alarm'] = "No Data"
        #self.generate_upload_data(data, parse_data)

        return parse_data

    # Upload Data

    def generate_upload_data(self, data, parse_data):

        """
        This function generates the upload data, which is a list containing 
        multiple parameters pertaining to the station. Ultimately, this data
        is upload to the table within the website.
        """

        if type(parse_data['volt']) == float: # Rounding to two decimals if applicable
            parse_data['volt'] = round(parse_data['volt'], 2)

        if type(parse_data['current']) == float:
            parse_data['current'] = round(parse_data['current'], 2)

        if parse_data['alarm'] != "No Data" and parse_data['alarm'] != global_variables.NOT_IMPLEMENTED_STRING:
            parse_data['alarm'] = global_variables.ALARM_INTERPRETATION[parse_data['alarm']]

        trimmed_time = data['transmit_time'].replace("T", " ", 1).replace("Z", "")
        local_format = "%Y-%m-%d %H:%M:%S %Z"

        utc_datetime_object = datetime.datetime.strptime(trimmed_time, local_format)
        utc_datetime_object = utc_datetime_object.replace(tzinfo = pytz.UTC)

        central = pytz.timezone("US/Central")
        central_datetime_object = utc_datetime_object.astimezone(central)

        self.upload_data = [self.number_label, data['latitude'], data['longitude'],
                            parse_data['alarm'], parse_data['jugs'], parse_data['current'],
                            parse_data['volt'], data['cep'], 
                            central_datetime_object.strftime(local_format) ]

        return None

    # High-Level functions

    def email_to_upload_data(self, imap_client):

        """
        This function is a high-level method that controls the all
        necessary steps to update the values of the water station
        to the southtexashrc website. These include the following:

        1 - Fetching the most recent email from the Rock Block
        2 - Break down in the info of the mail into separate lines that can be parsed.
        3 - Parse the hex data, which contains the sensory info.
            The universal_parsing_hex_data function only is concerned with
            the most current value of the variables from the emails
        4 - The complete_data_parsing_and_collection is gathers all
            the information contained within the hex data. Then this 
            data is placed into an Excel file within the csv_logger file.
        """

        uids = self.get_uids(imap_client, "New")

        if len(uids) == 0: # If no new emails, used the last one
            uids = [ self.get_uids(imap_client, "All")[-1] ]

        #print(uids)

        # Check all emails to get all data for excel file
        for uid in uids:

            email_body = self.fetch_email_body(imap_client, uid)
            print("Email Body: ")
            print(email_body)

            email_data = self.email_line_breaking(email_body)
            #print("Email Data")
            #print(email_data)

            parse_data = self.universal_parsing_hex_data(email_data)
            #print("Parse Data")
            #print(parse_data)

            self.complete_data_parsing_and_collection(email_data)

        # Only keep latest email upload data
        self.generate_upload_data(email_data, parse_data)

        return None


class PhaseOneStation(WaterStation):
    
    """
    This class is for the phase one stations.
    """

    def __init__(self, station_info):

        """
        This is the initialization function of the class.
        """

        WaterStation.__init__(self, station_info)
        self.phase_number = 1

        return None


class PhaseTwoStation(WaterStation):

    """
    This class is for the phase two stations.
    """

    def __init__(self, station_info):

        """
        This is the initialization function of the class.
        """

        WaterStation.__init__(self, station_info)
        self.phase_number = 2

        return None




