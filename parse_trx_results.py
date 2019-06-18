import glob
import os
import json
import pandas
import xml.etree.ElementTree as elTree
import re
import functools
import post_office
from datetime import datetime, timedelta, date


with open('config.json') as config_file:
    data = json.load(config_file)
PATH = data['path_to_test_results']
#PATH = data['path_debug']
DATETIME_FORMAT = data['datetime_format']
REPORT_NAME = data['report_name']


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
    """There are folders for each module,
    and there are daily folders in each module folder.
    Get a newest daily folder for each module.
    """
    daily_folders = []
    # Get the newest folder
    for folder in glob.glob(PATH):
        new_results = os.path.join(folder, datetime.today().strftime(DATETIME_FORMAT))
        i = 1
        while i != 3:
            if os.path.exists(new_results) and os.listdir(new_results):
                daily_folders.append(new_results)
                print('Folder found: ' + new_results)
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
                            #return [extract_scenario_num(test_name), step_with_error, error_list[line]]
                            return [test_name, step_with_error, error_list[line]]


def extract_scenario_num(text: str) -> str:
    """Get only scenario number without long name"""
    match = re.search(r'\d\d*_*\d\d*_*\d\d*_?\d*\d*', text)
    if match:
        return match.group().split('_')[-1]
    else:
        return text


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
    writer = pandas.ExcelWriter(REPORT_NAME, engine='xlsxwriter')
    workbook = writer.book

    # Format 'Result' cells for passed and failed tests
    format_green = workbook.add_format({'bold': 1, 'font_color': 'green'})
    format_red = workbook.add_format({'bold': 1, 'font_color': 'red'})

    header_format = workbook.add_format(data["header_format"])

    # Walk through the daily folders and create a worksheet wor each one
    for folder in get_daily_folders_list():
        path = folder + '\\*\\*.trx'
        split_path = [item for item in folder.split('\\') if item]  # remove empty strings
        rep_date = split_path[-1]
        theme = split_path[-2]
        file_name = '{}_{}'.format(rep_date, theme)
        header = data['table_header']

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


create_reports()
post_office.send_email()
