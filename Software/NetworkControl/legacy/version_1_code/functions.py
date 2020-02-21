# Common Core Libraries
import datetime
import time
import csv
import ftplib
import shutil
import sys
import os
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches

# Third-Party Libraries
import imapclient
import pyzmail
import logging
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import xlrd
import pandas as pd

# Local Imports
import global_variables

#----------------------------------------------------------------------------

# General Functions

def logging_setup(name):

	"""
	This function helps setup up the logging aspect of this project. This
	setup account for the rotation of the log files after every day. This
	is to ensure that the log file does not become too large.
	"""

	logger = logging.getLogger(name)
	logger.setLevel(logging.INFO)
	log_format = "%(levelname)s: %(asctime)-15s / %(message)s"

	print("LOGGER FILE PATH: " + global_variables.LOGGER_FILE_PATH)

	# Does not work with LINUX Systems
	log_handler = logging.handlers.TimedRotatingFileHandler(filename = global_variables.LOGGER_FILE_PATH,
															interval = 1, when = 'midnight')

	formatter = logging.Formatter(log_format)
	log_handler.setFormatter(formatter)
	log_handler.setLevel(logging.INFO)

	logger.addHandler(log_handler)

	return logger

def print_header(string):

	"""
	Helper function for creating a header fast.
	"""

	print("\n\n#####################################################################################")
	print("############################## {0} ###############################".format(string))
	print("#####################################################################################\n\n")

	return None

def imap_client_setup():

	"""
	This function helps the setup of the imap client.
	"""

	imap_client = imapclient.IMAPClient(global_variables.IMAP_SERVER, ssl = True)
	imap_client.login(global_variables.BOT_EMAIL, global_variables.BOT_EMAIL_PASSWORD)

	return imap_client

# File Management

def create_upload_and_save_files(water_stations_list, logger):

	"""
	This function handles the generation, upload, renaming, and archiving
	information files pertaining to the stations and the website.
	"""

	print_header("CREATING, UPLOADING, AND SAVING FILES")

	# Table File Upload
	table_file_name = create_file(water_stations_list, 'TABLE')
	upload_file(table_file_name, global_variables.WEBSITE['TABLE_CWD'])
	new_table_file = rename_and_save_file(table_file_name, 'TABLE')
	logger.info("Uploaded new TABLE file to the website, filename = {0}".format(new_table_file))

	# Marker File Upload
	update_all(global_variables.CSV_MARKER_FILE_PATH)
	logger.info("Uploaded/Updated marker data file to Google Drive.")
	
	# Station Collected Data Upload
	update_all(global_variables.CSV_FORMATTER_FILE_PATH)
	logger.info("Uploaded/Updated new COLLECTED DATA file to Google Drive")

	update_all(global_variables.WATER_LEVEL_CHARTS_PDF)
	logger.info("Updated water level charts to Google Drive")

	return None

def create_file(water_stations_list, type):

	"""
	This function simply creates a file, currently only CSV,
	depending on what type, TABLE or MARKER, that will later be uploaded
	to the website. 
	"""

	if type == 'TABLE':

		print("CREATING TABLE CSV FILE")

		csv_file_name = 'upload.csv'
		
		if sys.platform == "win32":
			file_path = '\\'.join(os.path.abspath(__file__).split('\\')[:-1]) + '\\'
			
		elif sys.platform == "linux":
			file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1]) + '/'
			
		csv_file_name = file_path + csv_file_name

		with open(csv_file_name, mode = 'w') as csv_file:

			csv_writer = csv.writer(csv_file, delimiter = ',', quotechar = '"',
									   quoting = csv.QUOTE_MINIMAL)

			csv_writer.writerow(['Station', 'Latitude', 'Longitude', 'Alarms', 'Gallons', 'Panel Current (A)', 'Battery Voltage (V)',
								 'CEP* (km)', 'Upload Time'])

			for water_station in water_stations_list:
				csv_writer.writerow(water_station.upload_data)

		return csv_file_name

	elif type == 'MARKER':

		print("CREATING MARKER CSV FILE")

		csv_file_name = 'station_marker_info.csv'
		
		if sys.platform == "win32":
			file_path = '\\'.join(os.path.abspath(__file__).split('\\')[:-1]) + '\\'
			
		elif sys.platform == "linux":
			file_path = '/'.join(os.path.abspath(__file__).split('/')[:-1]) + '/'
			
		csv_file_name = file_path + csv_file_name

		with open(csv_file_name, mode = 'w', newline='') as csv_file:

			csv_writer = csv.writer(csv_file, delimiter = ',', quotechar = '"',
									quoting = csv.QUOTE_MINIMAL)

			csv_writer.writerow(['id','map_id','address','description','pic','link','lat','lng','icon',
								 'anim','title','infoopen','category','approved','retina', 'type',
								 'did','other_data'])

			unique_markers = {}

			for water_station in water_stations_list:

				coordinate_set = str(water_station.latitude)+','+str(water_station.longitude)

				if coordinate_set not in unique_markers.keys():
					unique_markers[coordinate_set] = [str(water_station.number_label)]
				else:
					unique_markers[coordinate_set].append(str(water_station.number_label))

			for coordinate_set, stations_list in unique_markers.items():

				id = ''.join(stations_list)
				lat = coordinate_set.split(',')[0]
				lng = coordinate_set.split(',')[1]
			

				if len(stations_list) > 1:
					title = 'Stations ' + ', '.join(stations_list[:-1]) + ', and ' + stations_list[-1]
				else:
					title = 'Station ' + stations_list[0]

				csv_list = [id, '81', coordinate_set, '','','', lat, lng, '', '0', title, '0', '0', '1', '0', '0', '', '']
				csv_writer.writerow(csv_list)

		return csv_file_name

	return None

def upload_file(file, directory):

	"""
	This function uploads the 'file' within the 'directory' in the https://www.texassouthrc.com
	website server. 
	"""

	print("UPLOAD FILE: {0} TO DIRECTORY: {1}".format(file, directory))

	# Login to the website using file transfer protocol
	ftp = ftplib.FTP(global_variables.WEBSITE['SERVER_LOCATION'])
	ftp.login(user = global_variables.WEBSITE['USERNAME'], passwd = global_variables.WEBSITE['PASSWORD'])
	ftp.cwd(directory)

	# Uploading file
	local_upload = open(file, 'rb')
	
	if sys.platform == "win32":
		filename = file.split('\\')[-1]
	elif sys.platform == "linux":
		filename = file.split("/")[-1]
		
	print("FILENAME: " + filename)
	ftp.storbinary('STOR ' + filename, local_upload)
	local_upload.close()
	ftp.quit()

	return None

def rename_and_save_file(file, type):

	"""
	This function is used a way to keep a record of the upload files by
	'renaming' and 'saving' the file within a 'XXXX_records' depending
	on the type of file.
	"""

	print("RENAME AND SAVE FILE {0}, TYPE: {1}".format(file, type))

	if sys.platform == "win32":
		pure_file_name = file.split('\\')[-1]
	elif sys.platform == "linux":
		pure_file_name = file.split('/')[-1]

	time_stamp = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y-H%HM%MS%S')

	if type == 'TABLE':
		directory = global_variables.TABLE_RECORD_FOLDER
	elif type == 'MARKER':
		directory = global_variables.MARKER_RECORD_FOLDER
	else:
		raise RuntimeError("Unknown rename_and_save destination directory")

	# Does not work with LINUX systems
	cwd = os.path.dirname(os.path.abspath(__file__))

	if sys.platform == "win32":
		new_file = cwd + '\\' + directory + '\\' + pure_file_name + '-' + time_stamp + '.csv'
	elif sys.platform == "linux":
		new_file = cwd + '/' + directory + "/" + pure_file_name + '-' + time_stamp + ".csv"

	print(new_file)
	shutil.copyfile(file, new_file)

	return new_file

def autoplot_excel():

	"""
	This function helps with the autoploting of the excel files to create a visual
	representation of the data of the waterstations. The plots are accumulated into
	a PDF that is then uploaded to google drive. The website uses an iframe to show
	the PDF.
	"""

	xls = xlrd.open_workbook(global_variables.CSV_FORMATTER_FILE_PATH, on_demand=True)
	sheet_names = xls.sheet_names()

	frames = {}

	# Reading

	for current_sheet_name in sheet_names:

		frames[current_sheet_name] = pd.read_excel(global_variables.CSV_FORMATTER_FILE_PATH,
												   sheet_name = current_sheet_name)
	
		frames[current_sheet_name] = frames[current_sheet_name].sort_values(by="Time")
		frames[current_sheet_name] = frames[current_sheet_name].set_index("Time")

	# Writing

	writer = pd.ExcelWriter(global_variables.CSV_FORMATTER_FILE_PATH, engine='xlsxwriter')

	for current_sheet_name in sheet_names:

		frames[current_sheet_name].to_excel(writer, sheet_name=current_sheet_name)
		row, col = frames[current_sheet_name].shape

		workbook = writer.book
		worksheet = writer.sheets[current_sheet_name]

		chart = workbook.add_chart({'type': 'line'})
		colors = ['red','blue','green','purple','black','orange']

		line_name = list(frames[current_sheet_name].head(0))

		start_row = row - global_variables.AUTOPLOT_VALUE_SIZE_LIMIT
		if start_row <= 0:
			start_row = 1

		end_row = row

		for col_num in range(col):
			chart.add_series({
				'categories': [current_sheet_name, start_row, 0, end_row, 0],
				'values': [current_sheet_name, start_row, col_num + 1, end_row, col_num + 1],
				'line': {'color': colors[col_num]},
				'name': line_name[col_num],
			})

		chart.set_x_axis({'name': 'Time'})
		chart.set_y_axis({'name': 'Sensors and Weight'})

		worksheet.insert_chart('I3', chart, {'x_scale': 2, 'y_scale': 1.5})

	writer.save()

	# After plotting, create a pdf file of the graphs
	generate_charts_pdf()

	return None

def generate_charts_pdf():

	"""
	This is the method that actually handles the part of accumulating the plots and putting
	them into a single PDF for efficiency and convinience. This makes placing the plots into
	the website much easier.
	"""

	xls = xlrd.open_workbook(global_variables.CSV_FORMATTER_FILE_PATH, on_demand=True)
	sheet_names = xls.sheet_names()

	frames = {}

	# Reading

	for current_sheet_name in sheet_names:

		frames[current_sheet_name] = pd.read_excel(global_variables.CSV_FORMATTER_FILE_PATH,
												   sheet_name = current_sheet_name)
	
		frames[current_sheet_name] = frames[current_sheet_name].sort_values(by="Time")
		frames[current_sheet_name] = frames[current_sheet_name].set_index("Time")
		frames[current_sheet_name] = frames[current_sheet_name].loc[~frames[current_sheet_name].index.duplicated(keep='first')]

	# Creating PDF of Matplotlib Plots

	# Matplotlib settings
	font = {'size': 6}
	matplotlib.rc('font', **font)

	plots_pdf = PdfPages(global_variables.WATER_LEVEL_CHARTS_PDF)

	for current_sheet_name in sheet_names:

		figure_number = int(current_sheet_name.split('(')[0].replace("Station", "").strip())
		end_row, end_col = frames[current_sheet_name].shape

		start_row = end_row - global_variables.AUTOPLOT_VALUE_SIZE_LIMIT
		if start_row <= 0:
			start_row = 0

		line_name = list(frames[current_sheet_name].head(0))
		colors = ['r.-','b.-','g.-','m.-','k.-','c.-']

		time_column_data = list(frames[current_sheet_name].index)

		# Figure Settings
		plt_figure = plt.figure(figure_number)
		plt_figure.set_size_inches(15, 6) # 18.5, 10.5
		plt.title(current_sheet_name)
		plt.xlabel("Time")
		plt.ylabel("Sensors and Weight")
		plt.xticks(rotation=45)

		color_counter = 0
		for value_title in line_name:

			value_column_data = list(frames[current_sheet_name][value_title])
			plt.plot(time_column_data[start_row:end_row], value_column_data[start_row:end_row], colors[color_counter])
			color_counter += 1

		# Legends Settings
		legend_colors = ['red', 'blue', 'green', 'magenta', 'black', 'cyan']
		legend_colors = legend_colors[:len(line_name)]
		handle_list = [mpatches.Patch(color=legend_pair[0], label=legend_pair[1]) for legend_pair in zip(legend_colors, line_name)]
		plt.legend(handles=handle_list)

		# Post Value Adding Settings
		plt.tight_layout()

		# Saving Plots to PDF
		plots_pdf.savefig(plt_figure)

	#plt.show()
	plots_pdf.close()

#----------------------------------------------------------------------------

# Google Drive Functions

# File Handling and Merging

def google_drive_setup():

	"""
	This function handles with the authentication of the 
	google drive. Note that you need the client_secrets.json 
	file within the cwd to run this function. 
	"""

	google_login = GoogleAuth()
	google_login.LocalWebserverAuth()
	global_variables.GOOGLE_DRIVE = GoogleDrive(google_login)

	return None

def find_file(title, base):

	"""
	Due to the not-so-clever google API, finding a file
	within a google drive requires us to find the file manually. 
	This function does that operation.
	"""

	#print("\n\n***********************************")
	#print("Base: " + base)
	file_list = global_variables.GOOGLE_DRIVE.ListFile({'q': "'{0}' in parents".format(base)}).GetList()

	for file in file_list:

		if file == None:
			return None

		#print("title: {0}, id: {1}, mimeType: {2}\n".format(file['title'], file['id'], file['mimeType']))
		
		if file['title'] == title:
			return file

		if file['mimeType'].endswith('folder'):
			searched_file = find_file(title, file['id'])
			
			if searched_file != None:
				return searched_file

	return None

def download_and_relocate_file(file, destination):

	"""
	This function downloads and relocates the downloaded file
	to within the directory of this project.
	"""

	download_file = 'download_' + file['title']
	file.GetContentFile(download_file, remove_bom = True)

	if sys.platform == 'win32':
		relocated_download_file = destination + '\\' + download_file
		os.rename(download_file, relocated_download_file)
	
	elif sys.platform == 'linux':
		relocated_download_file = destination + '/' + download_file
		os.rename(download_file, relocated_download_file)

	return relocated_download_file

def merge_excel_files(receiving_file, appending_file):

	"""
	NOTE: This function is rather inefficient
	
	This function handles the merging of the local and remote
	excel that contains all the information of all the water
	stations. The remote file is within the trinity google email's 
	google drive.
	"""

	xls = xlrd.open_workbook(receiving_file, on_demand=True)
	sheet_names = xls.sheet_names()

	frames = {}

	# Reading all sheets and storing DataFrames into a dictionary
	for current_sheet_name in sheet_names:
	
		df1 = pd.read_excel(receiving_file, sheet_name = current_sheet_name)
		df2 = pd.read_excel(appending_file, sheet_name = current_sheet_name)
		df_list = [df1, df2]
	
		for df in df_list:
			df = df.sort_values(by="Time")
			df = df.set_index("Time")

		combined_df = pd.concat(df_list)
		combined_df = combined_df.loc[~combined_df.index.duplicated(keep='first')]
		combined_df = combined_df.sort_values(by="Time")
		combined_df = combined_df.set_index("Time")
		frames[current_sheet_name] = combined_df

	with pd.ExcelWriter(receiving_file) as writer:

		for current_sheet_name in frames.keys():

			if frames[current_sheet_name].empty == True:
				#print("Empty Dataframe")
				continue

			frames[current_sheet_name].to_excel(writer, sheet_name=current_sheet_name)

	# Autoplotting graphs
	autoplot_excel()

	return None

# High-Level Functions

def update_local_file(local_file, google_drive_file):

	"""
	This function updates a local file to match the file found
	in the trinity google mail's google drive.
	"""

	# Download File and relocate it near the original file
	if sys.platform == 'win32':
		local_file_directory = '\\'.join(local_file.split('\\')[:-1])
	elif sys.platform == 'linux':
		local_file_directory = '/'.join(local_file.split('/')[:-1])

	download_file = download_and_relocate_file(google_drive_file, local_file_directory)

	# Merge the values of the two excels
	merge_excel_files(local_file, download_file)

	# Delete the downloaded file
	os.remove(download_file)

	return None

def update_google_drive_file(local_file, google_drive_file = None):

	"""
	This function updates the file found in google drive of the 
	trinity google email.
	"""

	if sys.platform == "win32":
		local_file_title = local_file.split('\\')[-1]
	elif sys.platform == "linux":
		local_file_title = local_file.split('/')[-1]

	if google_drive_file == None:

		input = 'A'

		while input != "Y" and input != "y" and input != "N" and input != "n":
			input = input("{0}, would you like createa a google drive file? (Y/N)".format(name))
			input = input.replace("\n", "")
	
		if input == "Y" or input == "y":
			print("Yes")
			google_drive_file = global_variables.GOOGLE_DRIVE.CreateFile({'title':local_file_title})
		else:
			print("No")
			return None

	google_drive_file.SetContentFile(local_file)
	
	if local_file.endswith(".csv"):
		google_drive_file.Upload()
	else:
		google_drive_file.Upload({'convert': True})

	return None

def update_all(local_file):

	"""
	This email ensure that the local file and the remote (google drive)
	files are matching by updating them both. Instead of just overwriting 
	one of the files, we merge the data and then remove duplicates
	to ensure that all unique data is retained. This makes the implementation
	of new local computer's much easier.
	"""

	# Find file in Google Drive
	if sys.platform == 'win32':
		local_file_title = local_file.split('\\')[-1]
	elif sys.platform == 'linux':
		local_file_title = local_file.split('/')[-1]
		
	if local_file_title == global_variables.CSV_MARKER_FILE_PATH:
		local_file_title = "station_marker_info"

	google_drive_file = find_file(local_file_title, 'root')

	if google_drive_file != None:
		print("\n\nFound the File")
		print("title: {0}, id: {1}, mimeType: {2}".format(google_drive_file['title'], google_drive_file['id'], google_drive_file['mimeType']))
		
		if local_file.endswith('.xlsx'): # Excel File
			update_local_file(local_file, google_drive_file)
	
	else:
		print("File: " + local_file_title + " not found")
		print("update_local_file was avoided")

	update_google_drive_file(local_file, google_drive_file)

	return None




