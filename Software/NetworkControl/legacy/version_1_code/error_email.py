# Common Core Libraries
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Local Imports
import global_variables

#-------------------------------------------------------------------------
# Task: Sending Email to inform of error in Raspberry Pi

def main(subject, text):
    port = 465 # For SSL
    context = ssl.create_default_context()

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = global_variables.RASPBERRY_PI_EMAIL
    message["To"] = global_variables.PERSONAL_EMAIL

    text_part = MIMEText(text, "plain")
    message.attach(text_part)

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context = context) as server:
        server.login(global_variables.RASPBERRY_PI_EMAIL, global_variables.RASPBERRY_PI_EMAIL_PASSWORD)

        server.sendmail(global_variables.RASPBERRY_PI_EMAIL, 
                        global_variables.PERSONAL_EMAIL, 
                        message.as_string())
