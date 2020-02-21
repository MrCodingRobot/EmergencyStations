# Library Imports
import os
import sys
import shutil

# Third-Party Imports
import ftplib

# Local Imports
ROOT_DIR = os.path.abspath("../")
sys.path.append(ROOT_DIR)

import global_variables as gv
import utility as util

#-------------------------------------------------------------
# Class 

class DataUploader():

    def __init__(self):

        # Creating FTP session

        self.ftp = ftplib.FTP(gv.WEBSITE["SERVER_LOCATION"])
        self.ftp.login(user = gv.WEBSITE["USERNAME"], passwd= gv.WEBSITE["PASSWORD"])
        
        return None

    def upload_file(self, local_abs_file_path, server_destination_path):

        # Function for uploading files to the server

        self.ftp.cwd(server_destination_path)

        # Uploading file
        local_upload = open(local_abs_file_path, 'rb')

        # Determing filename for saving purposes
        if sys.platform == "win32":
            filename = local_abs_file_path.split('\\')[-1]
        elif sys.platform == "linux":
            filename = local_abs_file_path.split("/")[-1]

        # FTP file transport
        #print("FILENAME: " + filename)
        self.ftp.storbinary('STOR ' + filename, local_upload)
        local_upload.close()

        return None

    def upload_all_data_files(self):

        # Uploading all files within the generated_data folder

        for file in os.listdir(os.path.join(ROOT_DIR, gv.GENERATED_DATA_PATH)):
            
            if file.endswith(".pdf"): # PDF requires to be in a different path
                self.upload_file(os.path.join(ROOT_DIR, gv.GENERATED_DATA_PATH, file), gv.WEBSITE["PDF_UPLOAD_DIRECTORY"])    
            else:
                self.upload_file(os.path.join(ROOT_DIR, gv.GENERATED_DATA_PATH, file), gv.WEBSITE["UPLOAD_DIRECTORY"])

        return None

    def close(self):

        # Closing FTP session

        self.ftp.quit()
        self.ftp = None

        return None

    def create_ftp_session(self):

        # Restarting FTP session

        self.__init__()

        return None

