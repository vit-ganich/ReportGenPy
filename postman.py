import ssl
import smtplib
import os
import glob
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from Helpers.log_helper import init_logger
from Helpers.message_helper import MessageHelper
from Helpers.file_helper import FileHelper
from Helpers import config_reader as cfg, decorators as dec

logger = init_logger()


class Postman:

    email_sender = cfg.data['email_sender']
    email_passw = cfg.data['email_password']
    recipients = cfg.data['email_recipients']
    recipients_debug = cfg.data['email_recipients_debug']
    smtp_server = cfg.data['smtp_server']
    smtp_port = cfg.data['smtp_port']

    @classmethod
    @dec.measure_time
    def send_email(cls, report_file_to_send):
        """Get a report file from the script folder and send an email to the list of recipients"""
        logger.info("Start sending email")

        FileHelper.check_file_is_empty(report_file_to_send)

        context = ssl.create_default_context()

        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = cls.email_sender
        message["To"] = ','.join(cls.recipients)
        message["Subject"] = cfg.data['email_subject']
        message.preamble = 'CI results'

        cls.add_attachments(message, report_file=report_file_to_send, stats_graphs=True)
        # attach_embedded_stats_graphs(message)

        # Add body to email
        email_body = MessageHelper.create_email_body()
        message.attach(MIMEText(email_body, 'html'))

        with smtplib.SMTP_SSL(cls.smtp_server, cls.smtp_port, context=context) as server:
            server.login(cls.email_sender, cls.email_passw)
            server.sendmail(from_addr=cls.email_sender, to_addrs=cls.recipients, msg=message.as_string())
        logger.info("Email sent successfully to {} \n".format(cls.recipients))

    @classmethod
    def send_email_debug(cls, error_msg: str):
        """Send notification in case of something got wrong"""
        debug_message = "CI report wasn't sent - see the log below:\n{}\n{}".format(MessageHelper.get_debug_info(),
                                                                                    error_msg)

        context = ssl.create_default_context()

        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = cls.email_sender
        message["To"] = ','.join(cls.recipients_debug)
        message["Subject"] = "Daily CI Debug"

        # Add body to email
        message.attach(MIMEText(debug_message, "plain"))

        with smtplib.SMTP_SSL(cls.smtp_server, cls.smtp_port, context=context) as server:
            server.login(cls.email_sender, cls.email_passw)
            server.sendmail(from_addr=cls.email_sender, to_addrs=cls.recipients_debug, msg=message.as_string())

    @classmethod
    def add_attachments(cls, message: MIMEMultipart, report_file, stats_graphs=False):
        attachs_list = [report_file]

        if stats_graphs:
            for graph in glob.glob("Output\\*.png"):
                attachs_list.append(graph)

        for file in attachs_list:
            with open(file, "rb") as attachment:
                # Add file as application/octet-stream
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(file)))
                message.attach(part)

    @classmethod
    def attach_embedded_stats_graphs(cls, message: MIMEMultipart):
        """Insert images to email body"""
        files = [file for file in glob.glob("*.png")]
        msg_text = MIMEText('<br><img src="cid:{}"><br><img src="cid:{}">'.format(files[0], files[1]), 'html')
        message.attach(msg_text)

        for file in files:
            with open(file, 'rb') as f:
                image = MIMEImage(f.read())
            image.add_header('Content-ID', '<{}>'.format(file))
            message.attach(image)


if __name__ == "main":
    pass
