import ssl
import smtplib
import config_reader as cfg
import decorators as dec
import message_helper as msg_helper
import file_helper
import os
import glob
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from log_helper import init_logger


logger = init_logger()

email_sender = cfg.data['email_sender']
email_passw = cfg.data['email_password']
recipients = cfg.data['email_recipients']
recipients_debug = cfg.data['email_recipients_debug']
smtp_server = cfg.data['smtp_server']
smtp_port = cfg.data['smtp_port']

@dec.measure_time
def send_email(file=cfg.REPORT_FILE):
    """Get a report file from the script folder and send an email to the list of recipients"""
    logger.info("Start sending email")

    file_helper.check_file_is_empty(file)

    context = ssl.create_default_context()

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = email_sender
    message["To"] = ','.join(recipients)
    message["Subject"] = cfg.data['email_subject']
    message.preamble = 'CI results'

    with open(file, "rb") as attachment:
        # Add file as application/octet-stream
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(file)))
        message.attach(part)
    # Add body to email

    #message.attach(MIMEText(msg_helper.create_email_body(), 'html'))
    message.attach(MIMEText(msg_helper.create_email_body(), 'plain'))

    #embedded_images(message)
    
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(email_sender, email_passw)
        server.sendmail(from_addr=email_sender, to_addrs=recipients, msg=message.as_string())
    logger.info("Email sent successfully\n")


def send_email_debug(error_msg):
    debug_message = "CI report wasn't sent - see the log below:\n{}\n{}".format(msg_helper.get_debug_info(), error_msg)

    context = ssl.create_default_context()

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = email_sender
    message["To"] = ','.join(recipients_debug)
    message["Subject"] = "Daily CI Debug"

    # Add body to email
    message.attach(MIMEText(debug_message, "plain"))

    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(email_sender, email_passw)
        server.sendmail(from_addr=email_sender, to_addrs=recipients_debug, msg=message.as_string())


def embedded_images(message):
    files = [file for file in glob.glob("*.png")]
    msgText = MIMEText('P.S. <i>Some statistics</i> <b>(DEMO)</b>.<br><img src="cid:{}"><br><img src="cid:{}"><br>Generated with Pandas'.format(files[0], files[1]), 'html')
    message.attach(msgText)

    for file in files:
        with open(file, 'rb') as f:
            image = MIMEImage(f.read())
        image.add_header('Content-ID', '<{}>'.format(file))
        message.attach(image)
    
if __name__ == "main":
    pass
