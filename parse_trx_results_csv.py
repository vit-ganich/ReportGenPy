import glob
import os
import functools
import json
import re
import xml.etree.ElementTree as elTree
import smtplib
import ssl
import pandas
import xlsxwriter
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date


with open('config.json') as config_file:
    data = json.load(config_file)

#PATH = data['path_to_test_results']
PATH = data['path_debug']
REPORT_EXT = data['report_extension']
DATETIME_FORMAT = data['datetime_format']
HEADER = data['table_header']
DEL = data['delimiter']


def measure_time(foo):
    """Decorator for time measuring"""
    @functools.wraps(foo)
    def wrapper(*args, **kwargs):
        start_time = datetime.now().time()
        print('Started: {0}'.format(start_time))
        foo(*args, **kwargs)
        finish_time = datetime.now().time()
        print('Finished: {0}'.format(finish_time))
        diff = datetime.combine(date.min, finish_time) - datetime.combine(date.min, start_time)
        print("Total: " + str(diff))
    return wrapper


def get_daily_folders_list() -> list:
    """There are folders for each module,
    and there are daily folders in each module folder.
    Get a newest daily folder for each module.
    """
    daily_folders = []
    # Get the newest folder
    for folder in glob.glob(PATH):
        try:
            newest_folder = max(glob.glob(os.path.join(folder, '*/')), key=os.path.getmtime)
            # Check if the folder is not empty
            if os.listdir(newest_folder):
                daily_folders.append(newest_folder)
        except:
            print('No such folder: ' + folder)
    return daily_folders


def write_to_csv(path, file_name, header):
    with open(file_name + '.csv', 'w', encoding='utf-8') as report:  # encoding for Chinese characters
        report.write(header)
        for line in parse(path):
            report.write(line)


def write_to_xslx(path, file_name, header):
    writer = pandas.ExcelWriter(file_name + '.xlsx', engine='xlsxwriter')
    head = pandas.DataFrame(header)
    head.to_excel(writer, sheet_name='CI Results')
    for line in parse(path):
        data = pandas.DataFrame(line)
        data.to_excel(writer, sheet_name='CI Results')
    writer.save()



@measure_time
def create_reports():
    """Write a report for each folder with rest results"""
    for folder in get_daily_folders_list():
        path = folder + '*\\*.trx'
        split_path = folder.split('\\')
        rep_date = split_path[-2]
        theme = split_path[-3]
        product = '-'.join(split_path[-5:-3])
        #file_name = '{}_{}.{}'.format(rep_date, theme, REPORT_EXT)
        file_name = '{}_{}'.format(rep_date, theme)
        header = DEL.join((rep_date, product, theme, HEADER))

        write_to_xslx(path, file_name, header)
        # with open(file_name, 'w', encoding='utf-8') as report:  # encoding for Chinese characters
        #     report.write('{},{},{},,,,,,,,,,,,{}'.format(rep_date, product, theme, HEADER))
        #     #report.write(DEL.join((rep_date, product, theme, HEADER)))
        #     for line in parse(path):
        #         report.write(line)


def parse(path_to_folder: str) -> str:
    """Iterate through the files in specified folder"""
    for file in (item for item in glob.glob(path_to_folder, recursive=True)):
        file_name = file.split('\\')[-2:]
        ff_info = [item.replace('.trx', '') for item in file_name[1].split('_')]
        # Parts of feature info
        group = file_name[0].replace('CLTQACLIENT', '')
        ff_name = '_'.join(ff_info[:-5])
        database = ff_info[-3]
        browser = ff_info[-2]
        tail = ff_info[-1].split('-')
        build = tail[0]
        results = tail[1:]
        timing = results[0]
        total = results[-4]
        passed = results[-3]
        failed = results[-2]
        skipped = results[-1]
        error_message = ''
        result = 'PASSED'
        if int(failed):
            error_message = read_error_xml(file)
            result = 'FAILED'
        feature = DEL.join((group, ff_name, database, browser, build, timing, total,
                            passed, failed, skipped, result, error_message, '\n'))
        yield feature


def extract_scenario_num(text: str) -> str:
    """Get only scenario number without long name"""
    match = re.search(r'\d\d*_*\d\d*_*\d\d*_?\d*\d*', text)
    if match:
        return match.group().split('_')[-1]
    else:
        return text


def read_error_xml(file: str) -> str:
    """Open TRX file and read error messages"""
    tree = elTree.parse(file)
    root = tree.getroot()
    results = root.find('{http://microsoft.com/schemas/VisualStudio/TeamTest/2010}Results')

    for unitTesResult in results:
        if unitTesResult.attrib['outcome'] == 'Failed':
            test_name = unitTesResult.attrib['testName']
            for output in unitTesResult:
                for errorInfo in output:
                    error_list = [item for item in errorInfo.text.split('\n')]
                    for line in range(len(error_list)):
                        # Find an error in scenario output
                        if '-> error:' in error_list[line]:
                            # Step with error usually located at the previous line before error message
                            step_with_error = error_list[line - 1]
                            # But sometimes not the previous, so we search in upper lines
                            for i in range(2, 40):
                                # Scenarios always start with Gherkin keywords
                                if step_with_error.startswith(('Given', 'When', 'Then', 'And')):
                                    break
                                step_with_error = error_list[line - i]
                            return ('{},{},{}'.format(extract_scenario_num(test_name),
                                                      step_with_error,
                                                      error_list[line]))


def send_email():
    """Collect all report files in the script folder and send an email to the list of recipients"""
    server = data['smtp_server']
    port = data['smtp_port']
    login = data['email_sender']
    password = data['email_password']
    subject = data['email_subject']
    body = data['email_body']
    recipients = data['email_recipients']

    context = ssl.create_default_context()

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = login
    message["To"] = ','.join(recipients)
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    for file in glob.glob('*.csv'):
        with open(file, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"'
                            % os.path.basename(file))
            message.attach(part)

    with smtplib.SMTP_SSL(server, port, context=context) as server:
        server.login(login, password)
        server.sendmail(from_addr=login, to_addrs=recipients, msg=message.as_string())


def clear_folder():
    """Delete old reports"""
    for file in glob.glob('*.{}'.format(REPORT_EXT)):
        os.remove(file)

def convert_to_excel():
    for file in glob.glob('*.{}'.format(REPORT_EXT)):
        data_frame = pandas.read_csv(file, error_bad_lines=False)
        excel_writer = pandas.ExcelWriter(file.replace('.csv', '.xlsx'), engine='xlsxwriter')
        data_frame.to_excel(excel_writer, 'CI results')
        excel_writer.save()


clear_folder()
create_reports()
# send_email()
#convert_to_excel()
