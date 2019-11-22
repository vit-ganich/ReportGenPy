import glob
import os
import pandas
import xml.etree.ElementTree as elTree
import functools
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, date


"""This long script collects results from the specified folder and subfolders.

    Results stored in xlsx file with worksheets for each subfolder: 
    Classic, Horizon and Mobile (if they exist).
    After that the results file is sending to the recipients.
    """

PATH = "\\\\***\\TestResults\\CI\\V8\\FOUNDATION\\*"
#PATH = "\\\\w10x64-29\\Test Results\\CI\\V8\\Foundation\\*"
DATETIME_FORMAT = '%#m_%d_%Y'
REPORT_FILE = 'CI_Report_{}.xlsx'.format(datetime.today().strftime(DATETIME_FORMAT))
TABLE_HEADER = ["CI Group", "Feature", "DB type", "Browser", "Build", "Time", "Total", "Passed",
                "Failed", "Skipped", "Result", "Scenario", "Failed step", "Error message"]
HEADER_FORMAT = {
    "bold": "True",
    "text_wrap": "False",
    "valign": "center",
    "fg_color": "#D7E4BC",
    "border": 1
  }
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
EMAIL_LOGIN = '*****'
EMAIL_PASS = '****'
EMAIL_SUBJ = 'Daily CI results'
EMAIL_BODY = 'This is an email with attachment sent from Python'
EMAIL_ADDRESS_LIST = ['*****']


def measure_time(foo):
    """Decorator for time measuring"""
    @functools.wraps(foo)
    def wrapper(*args, **kwargs):
        start_time = datetime.now().time()
        foo(*args, **kwargs)
        finish_time = datetime.now().time()
        diff = datetime.combine(date.min, finish_time) - datetime.combine(date.min, start_time)
        print("|{}| time: {}".format(foo.__name__, diff))
    return wrapper


def get_daily_folders_list() -> list:
    """Get a newest daily folder for each module"""
    daily_folders = []
    # Get the newest folder
    for folder in glob.glob(PATH):
        new_results = os.path.join(folder, datetime.today().strftime(DATETIME_FORMAT))
        i = 1
        # If there are no folders for the last three days - break
        while i != 3:
            if os.path.exists(new_results) and os.listdir(new_results):
                daily_folders.append(new_results)
                break
            day_before = datetime.today() - timedelta(days=i)
            new_results = os.path.join(folder, day_before.strftime(DATETIME_FORMAT))
            i += 1
    return daily_folders


def read_error(file: str) -> list:
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
                            return [test_name, step_with_error, error_list[line]]


def parse(path_to_folder: str) -> list:
    """Iterate through the files in specified folder"""
    result_list = list()
    for file in [item for item in glob.glob(path_to_folder, recursive=True)]:
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
        error_message = ['-', '-', '-']
        result = 'PASSED'

        if int(failed):
            error_message = read_error(file)
            result = 'FAILED'

        feature = [*[group, ff_name, database, browser, build, timing, total,
                   passed, failed, skipped, result], *error_message]
        result_list.append(feature)
    return result_list


@measure_time
def create_reports():
    """Write a report for each folder with rest results"""
    writer = pandas.ExcelWriter(REPORT_FILE, engine='xlsxwriter')
    workbook = writer.book

    # Format 'Result' cells for passed and failed tests
    format_green = workbook.add_format({'bold': 1, 'font_color': 'green'})
    format_red = workbook.add_format({'bold': 1, 'font_color': 'red'})

    header_format = workbook.add_format(HEADER_FORMAT)

    # Walk through the daily folders and create a worksheet wor each one
    for folder in get_daily_folders_list():
        path = folder + '\\*\\*.trx'
        split_path = [item for item in folder.split('\\') if item]  # remove empty strings
        rep_date = split_path[-1]
        theme = split_path[-2]
        file_name = '{}_{}'.format(rep_date, theme)
        header = TABLE_HEADER

        data_frame = pandas.DataFrame(columns=header)
        # feature info to write to report
        tests_results = parse(path)
        data_frame = data_frame.append(pandas.DataFrame(tests_results, columns=header), ignore_index=True)
        data_frame.to_excel(writer, sheet_name=file_name)
        worksheet = writer.sheets[file_name]

        # Format failed cells
        worksheet.conditional_format('L1:L500', {'type': 'cell',
                                                 'criteria': '==',
                                                 'value': '"FAILED"',
                                                 'format': format_red})
        # Format passed cells
        worksheet.conditional_format('L1:L500', {'type': 'cell',
                                                 'criteria': '==',
                                                 'value': '"PASSED"',
                                                 'format': format_green})
        # Apply header format
        for col_num, value in enumerate(data_frame.columns.values):
            worksheet.write(0, col_num + 1, value, header_format)

    writer.save()


@measure_time
def send_email(file=REPORT_FILE):
    """Get a report file from the script folder and send an email to the list of recipients"""
    # To avoid sending an empty report
    if os.path.getsize(file) < 6000:
        raise FileNotFoundError

    context = ssl.create_default_context()

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = EMAIL_LOGIN
    message["To"] = ','.join(EMAIL_ADDRESS_LIST)
    message["Subject"] = EMAIL_SUBJ

    # Add body to email
    message.attach(MIMEText(EMAIL_BODY, "plain"))

    with open(file, "rb") as attachment:
        # Add file as application/octet-stream
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                        % os.path.basename(file))
        message.attach(part)

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(EMAIL_LOGIN, EMAIL_PASS)
        server.sendmail(from_addr=EMAIL_LOGIN, to_addrs=EMAIL_ADDRESS_LIST, msg=message.as_string())


create_reports()
send_email()
