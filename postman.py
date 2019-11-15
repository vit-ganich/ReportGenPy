import os
import ssl
import smtplib
import config_reader as cfg
import decorators as dec
import message_helper as msg_helper
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from log_helper import init_logger


logger = init_logger()


@dec.measure_time
def send_email(file=cfg.REPORT_FILE):
    """Get a report file from the script folder and send an email to the list of recipients"""
    logger.info("Start sending email")

    check_file_is_empty(file)

    email_sender = cfg.data['email_sender']
    recipients = cfg.data['email_recipients']

    context = ssl.create_default_context()

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = email_sender
    message["To"] = ','.join(recipients)
    message["Subject"] = cfg.data['email_subject']

    # Add body to email
    message.attach(MIMEText(msg_helper.create_email_body(), "plain"))

    with open(file, "rb") as attachment:
        # Add file as application/octet-stream
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{}"'.format(os.path.basename(file)))
        message.attach(part)

    with smtplib.SMTP_SSL(cfg.data['smtp_server'], cfg.data['smtp_port'], context=context) as server:
        server.login(user=cfg.data['email_sender'], password=cfg.data['email_password'])
        server.sendmail(from_addr=email_sender, to_addrs=recipients, msg=message.as_string())
    logger.info("Email sent successfully\n")


def check_file_is_empty(file, size_limit=6000):
    if os.path.getsize(file) < size_limit:
        os.remove(file)
        logger.warning('Report file \'{}\' is empty, email was not sent'.format(file))
        raise FileNotFoundError
    else:
        logger.info('Report file \'{}\' is ready '.format(file))


if __name__ == "main":
    pass
