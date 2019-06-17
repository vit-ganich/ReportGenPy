import glob
import os
import json
import pandas
import post_office
import parser
import decor


with open('config.json') as config_file:
    data = json.load(config_file)

PATH = data['path_to_test_results']
#PATH = data['path_debug']
DATETIME_FORMAT = data['datetime_format']


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


@decor.measure_time
def create_reports():
    """Write a report for each folder with rest results"""
    writer = pandas.ExcelWriter('Report.xlsx', engine='xlsxwriter')
    workbook = writer.book

    # Format 'Result' cells for passed and failed tests
    format_green = workbook.add_format({'bold': 1, 'font_color': 'green'})
    format_red = workbook.add_format({'bold': 1, 'font_color': 'red'})

    header_format = workbook.add_format(data["header_format"])

    #Walk through the daily folders and create a worksheet wor each one
    for folder in get_daily_folders_list():
        path = folder + '*\\*.trx'
        split_path = folder.split('\\')
        rep_date = split_path[-2]
        theme = split_path[-3]
        file_name = '{}_{}'.format(rep_date, theme)
        header = data['table_header']

        data_frame = pandas.DataFrame(columns=header)
        tests_results = parser.parse(path)
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
