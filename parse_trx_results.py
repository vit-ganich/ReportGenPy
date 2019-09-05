import glob
import os
import config_reader as cfg
import pandas
import xml.etree.ElementTree as elTree
import functools
import time
import postman
from datetime import datetime, timedelta
from log_helper import init_logger


logger = init_logger()

def measure_time(foo):
    """Decorator for time measuring"""
    @functools.wraps(foo)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        foo(*args, **kwargs)
        print("|%s| time: %1.1f sec" % (foo.__name__, time.time() - start_time))
    return wrapper

@measure_time
def create_reports():
    """Write a report for each folder with rest results"""
    writer = pandas.ExcelWriter(cfg.REPORT_FILE, engine='xlsxwriter')
    logger.info('Report file creation started')
    workbook = writer.book

    # Format 'Result' cells for passed and failed tests
    format_green = workbook.add_format({'bold': 1, 'font_color': 'green'})
    format_red = workbook.add_format({'bold': 1, 'font_color': 'red'})

    header_format = workbook.add_format(cfg.HEADER_FORMAT)

    # Walk through the daily folders and create a worksheet wor each one
    for folder in get_daily_folders_list():
        path = folder + '\\*\\*.trx'
        split_path = [item for item in folder.split('\\') if item]  # remove empty strings
        rep_date = split_path[-1]
        theme = split_path[-2]
        file_name = '{}_{}'.format(rep_date, theme)
        header = cfg.TABLE_HEADER

        tests_results = iterate_through_files_in_folder_and_parse_content(path)

        data_frame = pandas.DataFrame(columns=header)
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
    logger.info('Report file created successfully')


def get_daily_folders_list() -> list:
    daily_folders = []
    for folder in glob.glob(cfg.PATH):
        new_results = os.path.join(folder, datetime.today().strftime(cfg.DATETIME_FORMAT))
        days_from_now = 1
        # If there are no folders for the last three days - break
        while days_from_now != 3:
            if os.path.exists(new_results) and os.listdir(new_results):
                daily_folders.append(new_results)
                logger.info('Results folder found: ' + new_results)
                break
            day_before = datetime.today() - timedelta(days=days_from_now)
            new_results = os.path.join(folder, day_before.strftime(cfg.DATETIME_FORMAT))
            days_from_now += 1

    return daily_folders


def iterate_through_files_in_folder_and_parse_content(path_to_folder: str) -> list:
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
            error_message = open_trx_read_error(file)
            result = 'FAILED'

        feature = [*[group, ff_name, database, browser, build, timing, total,
                   passed, failed, skipped, result], *error_message]
        result_list.append(feature)
        logger.debug('Get feature info: {}'.format(feature))
    logger.info('Parsing files in folder: {} finished'.format(path_to_folder))

    return result_list


def open_trx_read_error(file: str) -> list:
    logger.debug('Reading the TRX file with errors')
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
                                    logger.debug('Step with error: {}'.format(step_with_error))
                                    break
                                step_with_error = error_list[line - i]
                            return [test_name, step_with_error, error_list[line]]


create_reports()
postman.send_email()
