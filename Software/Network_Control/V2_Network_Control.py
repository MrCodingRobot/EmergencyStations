#! /usr/bin/python3
#Network Control Code for Trinity University Water Station Project Phase I Version 2
#and
#Network Control Code for Trinity University Water Station Project Phase II Version 1
#Brian Guenther, Sean Farrell
#The purpose of this code is to take information sent through email by the satellite modules and upload that data through FTP to the website at Bluehost.com
#This code is written for Python 3 and will not work on earlier versions of python unless you change some of the libraries and commands.
#Furthemore, network security was not really considered here because the data being transferred is not valuable. Do not use this program to send valuable 
#or important information.

#For Phase II the first station is #6. Data sent from the satellite is in the following form
#An array called data that is 48 bytes long (0-47)*2:
#data[0] = station NUMBER
#data[1-43] = stored data between transmissions from station
#data[44] = index where last data was stored in data[1-43]
#data[45] = most recent weight (lbs)
#data[46] = most recent panel current (A)
#data[47] = most recent battery voltage (V)

#For Phase I there are 5 stations 1-5 Data sent from the satellite is in the following form
#data[0] = station #
#The following pattern is repeated for the rest of the array,where each set of readings is taken about an hour apart
#data[1] = weight sensor one raw reading
#data[2] = weight sensor two raw reading
#data[3] = weight sensor three raw reading
#data[4] = 3.3V reference voltage from arduinio

"""

"""




#Importing libraries
#Imapclient is used to get into the email server
#pyzmail is used to read the emails
#io is used to upload data to the sever without having to create a local file
#csv is used to create the file uploaded to the website
import imapclient, pyzmail, time, csv,datetime
#This is used to add a delay so that the program does not upload to the website every few seconds
from time import sleep

#ftpblib is used to upload information to the website using (file transfer protocol)
from ftplib import FTP

#The json file is used to convert the google map data into the file format needed for BlueHost
import json

#Whenever a new station is added, add the email here
Station_1_Email = '300234067639570@rockblock.rock7.com'
Station_2_Email = '300234067638500@rockblock.rock7.com'
Station_3_Email = '300234067638200@rockblock.rock7.com'
Station_4_Email = '300234067638620@rockblock.rock7.com'
Station_5_Email = '300234067431270@rockblock.rock7.com'
Station_6_Email = '300234067929930@rockblock.rock7.com'     #Phase 2 water station base


#This is is the email login and password that the satellite sends information to
BOT_EMAIL = 'trinitywaterstations@gmail.com'
BOT_EMAIL_PASSWORD = 'Water!Stations18'
IMAP_SERVER = 'imap.gmail.com'

#Initialize Upload Data
Upload_Data_1 = ['Station 1','Waiting for Data',' ',' ',' ',' ',' ',' ']
Upload_Data_2 = ['Station 2','Inactive',' ',' ',' ',' ',' ',' ']
Upload_Data_3 = ['Station 3','Inactive',' ',' ',' ',' ',' ',' ']
Upload_Data_4 = ['Station 4','Inactive',' ',' ',' ',' ',' ',' ']
Upload_Data_5 = ['Station 5','Inactive',' ',' ',' ',' ',' ',' ']
Upload_Data_6 = ['Station 6','Waiting for Data',' ',' ',' ',' ',' ',' ']

#Initialize Google Map Pin Upload Data
Station_num1 = 0
Station_num6 = 0
Jugs1 = 2019
Jugs2 = 2019
Longitude1 = 27.0215
Latitude1 = -98.1301
Longitude6 = 27.0354
Latitude6 = -98.1757


#This function checks to see if there is any new mail from Station_Email, it returns the number of emails from Station_Email
def check_email(Station_Email):
    #Connect to the email server and navigate to the main folder
   # imapCli = imapclient.IMAPClient(IMAP_SERVER, ssl=True)
   # imapCli.login(BOT_EMAIL, BOT_EMAIL_PASSWORD)
    imapCli.select_folder('INBOX')
    #Find the number of emails from the satellite and return this number
    UIDs = imapCli.search(['FROM', Station_Email])
   # imapCli.logout()
    return len(UIDs)


#This function reads all emails from Station_Email and parses the information grabbing the latitude, longitude, accuracy, and data sent. It returns these values as Upload_Data[]
def get_instructions(Station_Email):

    #Connect to the email server and navigate to the main folder
    #print('Connecting to IMAP server at %s...' % (IMAP_SERVER))
   # imapCli = imapclient.IMAPClient(IMAP_SERVER, ssl=True)
   # imapCli.login(BOT_EMAIL, BOT_EMAIL_PASSWORD)
    imapCli.select_folder('INBOX')

    # Fetch all emails from the satellite
    instructions = [] #Used to hold parsed text from the body of the email
    #Find all the emails from the satellite and save their unique identifier (UID code)
    UIDs = imapCli.search(['FROM', Station_Email])
    #print(len(UIDs))
    #Grab the data from the body of all of the messages from the satellite
    rawMessages = imapCli.fetch(UIDs, ['BODY[]'])
    for UID in rawMessages.keys():
            # Parse the raw email message.
            message = pyzmail.PyzMessage.factory(rawMessages[UID][b'BODY[]'])
            if message.html_part != None:
                body = message.html_part.get_payload().decode(message.html_part.charset)
            if message.text_part != None:
                # If there's both an html and text part, use the text part.
                body = message.text_part.get_payload().decode(message.text_part.charset)
            #Add the message body to the instructions
            instructions.append(body)

    #Sort through the instruction array and grab the Hex encoded data, the latitude and longitude
    #and the CEP or the relative error of the latitude and longitude values
    for instruction in instructions:
        lines = instruction.split('\n')
        for line in lines:
             if line.startswith('Data'):
                 HEX_DATA = line[6:(len(line)-1)]
             elif line.startswith('Iridium Latitude'):
                 Latitude = line[18:(len(line)-1)]
             elif line.startswith('Iridium Longitude'):
                 Longitude = line[19:(len(line)-1)]
             elif line.startswith('Iridium CEP'):
                 CEP = line[13:(len(line)-1)]

    #Convert Hexadecimal data from email to plain text
    #Grab the station number and jugs from the data and save them separately
    #INSERT IF ELSE HERE TO ASSIGN DIFFERENT STATION NUMBER BASED ON EMAIL

    #This if statement reads the first 2 bytes of the data array to determine station NUMBER
    #if the station number is 6 (Phase 2 station) the data needs to be decoded differently
    if(Station_Email  == Station_6_Email):
       # TEXT_DATA = map(ord, HEX_DATA.decode('hex'))
        TEXT_DATA = bytearray.fromhex(HEX_DATA)
        Station_num = TEXT_DATA[0]
        #
        WSIndex = (2+(TEXT_DATA[44]*3))       #index for where previous data stored in array
        WS_current_weight = float(TEXT_DATA[45])
        WS_current_amps = (float(TEXT_DATA[46])/10)
        WS_current_volt = (float(TEXT_DATA[47])/10)
        print ('Water Station current weight (lbs): ', WS_current_weight)
        print ('Water Station current panel current (A)', WS_current_amps)
        print ('Water Station current battery voltage (V)', WS_current_volt)
        #
        JugWeight = 8.34 #(lbs) of US gallon of water at 62 (F) or 17 (C)
        Jugs = round((WS_current_weight/JugWeight),0)
        Current = WS_current_amps
        Battery_Voltage = WS_current_volt

        #if previous data is stored in array
        if(WSIndex != 2 ):			#2 is used because array fills at an offset of 2 indeces
            WS_old_weight = float(TEXT_DATA[WSIndex])
            WS_old_amps = (float(TEXT_DATA[WSIndex+1])/10)
            WS_old_volt = (float(TEXT_DATA[WSIndex+2])/10)

            WS_avg_weight = (WS_current_weight+WS_old_weight)/2
            WS_avg_amps = (WS_current_amps+WS_old_amps)/2
            WS_avg_volt = (WS_current_volt+WS_old_volt)/2
            #
            Jugs =round(( WS_avg_weight/JugWeight),0)
            Current = WS_avg_amps
            Battery_Voltage = WS_avg_volt

        print(Station_Email)
        print(Jugs)
        #Get Current Time
        Current_Time = str(datetime.datetime.now())[0:16]

    else:
        #Convert Hexadecimal data from email to plain text
        TEXT_DATA = bytearray.fromhex(HEX_DATA).decode()
        Station_num = 1
        #
        WS3LatestRead = TEXT_DATA[42:45]
        WS2LatestRead = TEXT_DATA[39:42]
        WS1LatestRead = TEXT_DATA[36:39]
        print(WS3LatestRead)
        print(WS2LatestRead)
        print(WS1LatestRead)
        WS3LatestRead_int = int(WS3LatestRead,10)
        WS2LatestRead_int = int(WS2LatestRead,10)
        WS1LatestRead_int = int(WS1LatestRead,10)
        Avg = (WS3LatestRead_int+WS2LatestRead_int+WS1LatestRead_int)/3

        if Avg < 190:
            Jugs =  -1
        elif 190<Avg<210:
            Jugs = 0
        elif 210<Avg<235:
            Jugs = 1
        elif 230<Avg<255:
            Jugs = 2
        elif 255<Avg<280:
            Jugs = 3
        elif 280<Avg<300:
            Jugs = 4
        elif 300<Avg<320:
            Jugs = 5
        elif 320<Avg<340:
            Jugs = 6
        elif 340<Avg<365:
            Jugs = 7
        elif 365<Avg<385:
            Jugs = 8
        elif 385<Avg<405:
            Jugs = 9
        elif 405<Avg<430:
            Jugs = 10
        elif 430<Avg<462:
            Jugs = 11
        elif 462<Avg<470:
            Jugs = 12
        elif 470<Avg:
            Jugs = 13

        print(Station_Email)
        print(Jugs)
        #Get Current Time
        Current_Time = str(datetime.datetime.now())[0:16]
        #Phase 1 doesn't have capabilities to read station current and Voltage
        Current = 0
        Battery_Voltage = 0


    #Combine data and longitude/latitude information into one string
    Upload_Data= [Station_num,Jugs,Longitude,Latitude,CEP,Current_Time,Current,Battery_Voltage]
    #Print that data has been received
    print('Data received:'),
    print(Current_Time)
    #Deletes the email we just read the data from
    if len(UIDs) > 0:
        imapCli.delete_messages(UIDs)
       # imapCli.logout()
    #This function uploads the station data onto a google map
    Upload_to_GoogleMap(Station_num,Jugs,Longitude,Latitude,CEP,Current_Time,Current,Battery_Voltage)

    return Upload_Data

#This function serves to create a CSV file to hold the data, then writes the data into it, then logs
#into the website and uploads the data there
def Upload_to_Website(Upload_Data_1,Upload_Data_2,Upload_Data_3,Upload_Data_4,Upload_Data_5,Upload_Data_6):
    #Make CSV file to hold the data, and write in the data
    with open('Upload.csv',mode='w') as Upload_file:
        Upload_writer=csv.writer(Upload_file,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
        Upload_writer.writerow(['Station','# Jugs','Longitude','Latitude','CEP','Upload Time','Current','Battery Voltage'])
        Upload_writer.writerow(Upload_Data_1)
        Upload_writer.writerow(Upload_Data_2)
        Upload_writer.writerow(Upload_Data_3)
        Upload_writer.writerow(Upload_Data_4)
        Upload_writer.writerow(Upload_Data_5)
        Upload_writer.writerow(Upload_Data_6)
    #Login to the website using file transfer protocol
    ftp=FTP('50.87.249.20') #Set location of server
    ftp.login(user='southti6',passwd = 'Water!Station18') #Login to website
    ftp.cwd('/Water_Station/Sat_comm_test/') #Change to appropriate folder
    #Upload File
    Local_Upload = open('Upload.csv','rb')
    ftp.storbinary('STOR Upload.csv',Local_Upload)
    Local_Upload.close()
    ftp.quit()

#This function is used to upload each stations information onto BlueHost, where
#the JSON file will be read and put a marker with the stations information on
#a google map.
def Upload_to_GoogleMap(Station_num,Jugs,Longitude,Latitude,CEP,Current_Time,Current,Battery_Voltage):
    #code below updates marker parameters needed for google map
   
    if (Station_num == 1):
        Station_num1 = Station_num
        Jugs1 = Jugs
        Longitude1 = Longitude
        Latitude1 = Latitude
    if(Station_num == 6):
        Station_num6 = Station_num
        Jugs6 = Jugs
        Longitude6 = Longitude
        Latitude6 = Latitude

	#code below creates  map that eil be sent to BlueHost in a .json file	
    my_station = {
        "creator": "Daniel and Sean",
        "version": None,
        "json_version": "1.01",
        "maps": [
            {
                "id": "81",
                "map_title": "Water Station Phase 2",
                "map_width": "100",
                "map_height": "400",
                "map_start_lat": "29.4487",
                "map_start_lng": "-98.4451",
                "map_start_location": "29.4487,-98.4451",
                "map_start_zoom": "1",
                "default_marker": "https:\/\/www.wpgmaps.com\/wp-content\/uploads\/2019\/01\/5c3db2e7ea3c44.37472676-1.png",
                "type": "1",
                "alignment": "2",
                "directions_enabled": "1",
                "styling_enabled": "0",
                "styling_json": "",
                "active": "0",
                "kml": "",
                "bicycle": "2",
                "traffic": "2",
                "dbox": "5",
                "dbox_width": "100",
                "listmarkers": "0",
                "listmarkers_advanced": "0",
                "ugm_enabled": "2",
                "fusion": "",
                "map_width_type": "\\%",
                "map_height_type": "px",
                "mass_marker_support": "2",
                "ugm_access": "2",
                "order_markers_by": "1",
                "order_markers_choice": "2",
                "show_user_location": "2",
                "filterbycat": "0",
                "ugm_category_enabled": "2",
                "default_to": "",
                "other_settings": "a:30:{s:19:\"store_locator_style\";s:6:\"legacy\";s:33:\"wpgmza_store_locator_radius_style\";s:6:\"legacy\";s:20:\"directions_box_style\";s:6:\"modern\";s:22:\"wpgmza_dbox_width_type\";s:1:\"%\";s:12:\"map_max_zoom\";s:1:\"3\";s:12:\"map_min_zoom\";s:2:\"21\";s:15:\"sl_stroke_color\";s:0:\"\";s:17:\"sl_stroke_opacity\";s:0:\"\";s:13:\"sl_fill_color\";s:0:\"\";s:15:\"sl_fill_opacity\";s:0:\"\";s:15:\"click_open_link\";i:2;s:15:\"transport_layer\";i:2;s:16:\"iw_primary_color\";s:6:\"2A3744\";s:15:\"iw_accent_color\";s:6:\"252F3A\";s:13:\"iw_text_color\";s:6:\"FFFFFF\";s:14:\"wpgmza_iw_type\";s:1:\"0\";s:15:\"list_markers_by\";s:1:\"0\";s:11:\"push_in_map\";s:0:\"\";s:21:\"push_in_map_placement\";s:1:\"9\";s:24:\"wpgmza_push_in_map_width\";s:0:\"\";s:25:\"wpgmza_push_in_map_height\";s:0:\"\";s:17:\"wpgmza_theme_data\";s:0:\"\";s:24:\"upload_default_ul_marker\";s:0:\"\";s:24:\"upload_default_sl_marker\";s:0:\"\";s:21:\"rtlt_route_col_normal\";s:6:\"5FA8E8\";s:20:\"rtlt_route_col_hover\";s:6:\"98CFFF\";s:18:\"rtlt_route_opacity\";s:3:\"0.6\";s:20:\"rtlt_route_thickness\";s:2:\"12\";s:26:\"upload_default_rtlt_marker\";s:0:\"\";s:24:\"wpgmza_ugm_upload_images\";i:2;}"
            }
        ],
        "categories": [
            {
                "id": "2",
                "active": "0",
                "category_name": "To Rent",
                "category_icon": "",
                "retina": "0",
                "parent": "0",
                "priority": "0",
                "image": None,
                "map_id": "0"
            },
            {
                "id": "1",
                "active": "0",
                "category_name": "For Sale",
                "category_icon": "",
                "retina": "0",
                "parent": "0",
                "priority": "0",
                "image": None,
                "map_id": "0"
            },
            {
                "id": "4",
                "active": "0",
                "category_name": "Houses",
                "category_icon": "",
                "retina": "0",
                "parent": "2",
                "priority": "0",
                "image": None,
                "map_id": "0"
            },
            {
                "id": "6",
                "active": "0",
                "category_name": "Apartments",
                "category_icon": "",
                "retina": "0",
                "parent": "2",
                "priority": "0",
                "image": None,
                "map_id": "0"
            },
            {
                "id": "3",
                "active": "0",
                "category_name": "Houses",
                "category_icon": "",
                "retina": "0",
                "parent": "1",
                "priority": "0",
                "image": None,
                "map_id": "0"
            },
            {
                "id": "5",
                "active": "0",
                "category_name": "Apartments",
                "category_icon": "",
                "retina": "0",
                "parent": "1",
                "priority": "0",
                "image": None,
                "map_id": "0"
            }
        ],
        "customfields": [
            {
                "id": "1",
                "name": "Price",
                "icon": "fa-dollar",
                "attributes": "{\"type\":\"number\",\"min\":\"0\",\"step\":\"0.01\"}",
                "widget_type": "range-slider"
            },
            {
                "id": "3",
                "name": "Take Aways",
                "icon": "icon-food",
                "attributes": "{\"Resturaunt\":\"1\"}",
                "widget_type": "checkboxes"
            }
        ],
        "markers": [
            {
                "id": "6435",
                "map_id": "81",
                "address": str(Latitude1)+","+str(Longitude1), #"29.4487,-98.4451",
                "description": "Water station, number of water jugs = "+str(Jugs1) ,
                "pic": "",
                "link": "",
                "lat": str(Latitude1), #"29.4487",
                "lng": str(Longitude1), #"-98.4451",
                "icon": "",
                "anim": "0",
                "title": "Water Station number: "+str(Station_num1),
                "infoopen": "0",
                "category": "0",
                "approved": "1",
                "retina": "0",
                "type": "0",
                "did": "",
                "other_data": ""
            },
            {
                "id": "6436",
                "map_id": "81",
                "address": str(Latitude6)+","+str(Longitude6), #"29.4487,-98.4451",
                "description": "Water station, number of water jugs = "+str(Jugs6) ,
                "pic": "",
                "link": "",
                "lat": str(Latitude6), #"29.4487",
                "lng": str(Longitude6), #"-98.4451",
                "icon": "",
                "anim": "0",
                "title": "Water Station number: "+str(Station_num6),
                "infoopen": "0",
                "category": "0",
                "approved": "1",
                "retina": "0",
                "type": "0",
                "did": "",
                "other_data": ""
            }
        ],
        "circles": [],
        "polygons": [],
        "polylines": [],
        "rectangles": [],
        "datasets": []
    }

    with open('Station.json', 'w') as json_file:
        json.dump(my_station, json_file)

    #Login to the website using file transfer protocol
    ftp=FTP('50.87.249.20') #Set location of server
    ftp.login(user='southti6',passwd = 'Water!Station18') #Login to website
    #log into public file so that google maps can load file from database
    ftp.cwd('/public_html/Testing_Import_for_CSV/') #Change to appropriate folder
    #Upload File
    Local_Upload = open('Station.json','rb')
    ftp.storbinary('STOR Station.json',Local_Upload)
    Local_Upload.close()
    ftp.quit()
    print('Uploaded Water Sation '+str(Station_num)+" to BlueHost for google Map")

print('Email bot started. Press Ctrl-C to quit.')
#imapCli= imapclient.IMAPClient(IMAP_SERVER,ssl=True)
#imapCli.login(BOT_EMAIL,BOT_EMAIL_PASSWORD)

while True:
    imapCli=imapclient.IMAPClient(IMAP_SERVER,ssl=True)
    imapCli.login(BOT_EMAIL,BOT_EMAIL_PASSWORD)
    New_mail_1 = check_email(Station_1_Email) #Check to see if any emails from station1 have been sent

    #If one has then save the information sent as Upload_Data_1
    if(New_mail_1 > 0):
        Upload_Data_1 = get_instructions(Station_1_Email)

    New_mail_2 = check_email(Station_2_Email)
    if(New_mail_2 > 0):
        Upload_Data_2 = get_instructions(Station_2_Email)

    New_mail_3 = check_email(Station_3_Email)
    if(New_mail_3 > 0):
        Upload_Data_3 = get_instructions(Station_3_Email)

    New_mail_4 = check_email(Station_3_Email)
    if(New_mail_4>0):
        Upload_Data_4 = get_instructions(Station_4_Email)

    New_mail_5 = check_email(Station_5_Email)
    if(New_mail_5>0):
        Upload_Data_5 = get_instructions(Station_5_Email)
    ###Phase 2 water station base###
    New_mail_6 = check_email(Station_6_Email)
    if(New_mail_6>0):
        Upload_Data_6 = get_instructions(Station_6_Email)


    Upload_to_Website(Upload_Data_1,Upload_Data_2,Upload_Data_3,Upload_Data_4,Upload_Data_5,Upload_Data_6)
    imapCli.logout()
    sleep(600)
