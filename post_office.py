import os
import json
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



def send_email():
    """Get a report file from the script folder and send an email to the list of recipients"""
    with open('config.json') as config_file:
        data = json.load(config_file)
    server = data['smtp_server']
    port = data['smtp_port']
    login = data['email_sender']
    password = data['email_password']
    subject = data['email_subject']
    body = data['email_body']
    recipients = data['email_recipients']
    file = data['report_name']
    # To avoid sending an empty report
    if os.path.getsize(file) < 6000:
        raise FileNotFoundError

    context = ssl.create_default_context()

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = login
    message["To"] = ','.join(recipients)
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    with open(file, "rb") as attachment:
        # Add file as application/octet-stream
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                        % os.path.basename(file))
        message.attach(part)

    with smtplib.SMTP_SSL(server, port, context=context) as server:
        server.login(login, password)
        server.sendmail(from_addr=login, to_addrs=recipients, msg=message.as_string())


if __name__ == 'main':
    pass
