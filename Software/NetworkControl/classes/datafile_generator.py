# Library Imports
import os
import sys
import shutil

# Third-Party Library Imports
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import fpdf

# Local Imports
ROOT_DIR = os.path.abspath("../")
sys.path.append(ROOT_DIR)

import global_variables as gv
import utility as util

#-------------------------------------------------------------
# Class 

class DatafileGenerator():

    def __init__(self):

        return None

    def generate_latest_data_table(self, mysql_table_df):

        self.table_df = {"Station #": [],
                         "Upload Time": [],
                         "Jugs": [],
                         "Latitude": [],
                         "Longitude": []}

        for station in gv.STATION_INFO:

            sta_i = station["email"] # station index

            self.table_df["Station #"].append(station["number"])

            # Grabbing the first index
            first_index = mysql_table_df[sta_i].index[0]
            timezone = mysql_table_df[sta_i].loc[first_index,"timezone"]
            
            # Generating a time string that includes timezone if timezone is found
            time_string = str(first_index)
            if timezone is not None: 
                time_string += " " + timezone
            
            # Creating the dictionary to later create the dataframe
            self.table_df["Upload Time"].append(time_string)
            self.table_df["Jugs"].append(int(round(mysql_table_df[sta_i].loc[first_index,"weight_lbs"] / gv.JUG_WEIGHT)))
            self.table_df["Latitude"].append(mysql_table_df[sta_i].loc[first_index,"latitude"])
            self.table_df["Longitude"].append(mysql_table_df[sta_i].loc[first_index,"longitude"])

        # Creating the dataframe
        self.table_df = pd.DataFrame(self.table_df)
        self.table_df = util.sort_and_clean_df(self.table_df, "Station #", True) 
        
        # Saving the TABLE csv file
        table_csv_path = os.path.join(ROOT_DIR, gv.TABLE_STORAGE_PATH)
        self.table_df.to_csv(table_csv_path)
        
        return None
        
    def generate_plots(self, mysql_table_df):

        # Making PNGs: http://queirozf.com/entries/pandas-dataframe-plot-examples-with-matplotlib-pyplot
        # Saving PNGs to PDF: https://stackoverflow.com/a/27327984

        for station in gv.STATION_INFO:

            sta_i = station["email"] # station index
            title = "Station " + str(station["number"])
            filename = title.replace(" ","") + ".png"

            # Grabing certain columns that will be used to plot the graph
            plot_df = mysql_table_df[sta_i][["sensor_1","sensor_2","sensor_3","reference","weight_lbs"]]
            
            # Plotting the data with matplotlib.pyplot
            plot_df.plot(y=["sensor_1","sensor_2","sensor_3","reference","weight_lbs"],
                         title=title,
                         legend=True,
                         grid=True,
                         figsize=(8,5))
            
            # Saving the plot
            plot_png_path = os.path.join(ROOT_DIR, gv.PLOT_STORAGE_PATH, filename)
            plt.savefig(plot_png_path)

        png_directory = os.path.join(ROOT_DIR, gv.PLOT_STORAGE_PATH)

        # Converting all PNGs to one PDF
        pdf = fpdf.FPDF(orientation="L")

        for file_path in os.listdir(png_directory):
            
            if file_path.endswith(".png"):
                pdf.add_page()
                pdf.image(os.path.join(png_directory, file_path))

        # Saving the PDF file
        plot_pdf_path = os.path.join(ROOT_DIR, gv.PDF_STORAGE_PATH)
        pdf.output(plot_pdf_path, "F")

        return None

    def generate_station_markers(self, mysql_table_df):

        station_locations = {}
        
        self.markers_df = {"id": [],
                           "map_id": [],
                           "address": [],
                           "description": [],
                           "pic": [],
                           "link": [],
                           "lat": [],
                           "lng": [],
                           "icon": [],
                           "anim": [],
                           "title": []
                           }

        # Determining if stations share same latitude and longitude coordinates
        # Then making same latitude and longitude entries into one row entry

        for station in gv.STATION_INFO:

            sta_i = station["email"] # station index
            first_index = mysql_table_df[sta_i].index[0]

            lat_lon = tuple(mysql_table_df[sta_i].loc[first_index, ["latitude","longitude"]])
            
            if lat_lon not in station_locations.keys():
                station_locations[lat_lon] = str(station["number"])
            else:
                station_locations[lat_lon] += str(station["number"])

        # Now creating the dataframe with the lat_lon pairs and placing other necessary
        # columns into a CSV to later upload

        for lat_lon_tuple, station_numbers in station_locations.items():

            # First placing unique data

            self.markers_df["id"].append(station_numbers)
            self.markers_df["address"].append(str(lat_lon_tuple).replace("(","").replace(")", ""))
            self.markers_df["lat"].append(lat_lon_tuple[0])
            self.markers_df["lng"].append(lat_lon_tuple[1])

            # Generating title string
            title_string = ""

            for number in station_numbers:
                if title_string == "":
                    title_string += "Station " + number
                else:
                    title_string += ", Station " + number

            self.markers_df["title"].append(title_string)

        # Now entering universal data to conform with google maps API

        number_of_rows = len(station_locations.keys())

        self.markers_df["map_id"] = [81 for i in range(number_of_rows)]
        self.markers_df["description"] = [None for i in range(number_of_rows)]
        self.markers_df["pic"] = [None for i in range(number_of_rows)]
        self.markers_df["link"] = [None for i in range(number_of_rows)]
        self.markers_df["icon"] = [None for i in range(number_of_rows)]
        self.markers_df["anim"] = [0 for i in range(number_of_rows)]
        self.markers_df["infoopen"] = [0 for i in range(number_of_rows)]
        self.markers_df["category"] = [0 for i in range(number_of_rows)]
        self.markers_df["approved"] = [1 for i in range(number_of_rows)]
        self.markers_df["retina"] = [0 for i in range(number_of_rows)]
        self.markers_df["type"] = [0 for i in range(number_of_rows)]
        self.markers_df["did"] = [None for i in range(number_of_rows)]
        self.markers_df["other_data"] = [None for i in range(number_of_rows)]
        
        # Creating pandas dataframe, sorting it, and cleaning the dataframe
        self.markers_df = pd.DataFrame(self.markers_df)
        self.markers_df = util.sort_and_clean_df(self.markers_df, "id", True)

        # Saving the dataframe into a CSV file
        markers_csv_path = os.path.join(ROOT_DIR,gv.MARKERS_STORAGE_PATH)
        self.markers_df.to_csv(markers_csv_path)

        return None