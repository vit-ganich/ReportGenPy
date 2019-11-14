import os
import ssl
import smtplib
import config_reader as cfg
import parse_trx_results as parser
import decorators as dec
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from log_helper import init_logger


logger = init_logger()

summary_pattern = """------------ Theme: {}
Total tests  count: {}
Passed tests count: {}
Failed tests count: {}
Passed: {} %

"""

email_footer = """
Python-generated email with the CI test results spreadsheet.
If you want to unsubscribe, please, click |HERE| or just email to vhanich@elinext.com.
"""

email_subject = "Daily CI Report"

def create_email_body():
    message = []
    try:
        for item in parser.brief_summary:
           message.append(summary_pattern.format(item[0], item[1], item[2], item[3], item[4]))
    except Exception as e:
        logger.warning("Can't create brief summary: " + e.message)
    finally:
        return "".join(message) + email_footer


@dec.measure_time
def send_email(file=cfg.REPORT_FILE):
    """Get a report file from the script folder and send an email to the list of recipients"""
    email_sender = cfg.data['email_sender']
    recipients = cfg.data['email_recipients']

    check_file_is_empty(file)
    context = ssl.create_default_context()

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = email_sender
    message["To"] = ','.join(recipients)
    message["Subject"] = email_subject

    # Add body to email
    #message.attach(MIMEText(cfg.data['email_body'], "plain"))
    message.attach(MIMEText(create_email_body(), "plain"))

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
