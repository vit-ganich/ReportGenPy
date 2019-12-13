import glob
import os
import pandas
from Helpers.trx_helper import TrxHelper
from stats import Stats
from Helpers import config_reader as cfg, decorators as dec
from datetime import datetime, timedelta
from Helpers.log_helper import init_logger
from Helpers.file_helper import FileHelper

logger = init_logger()


class TrxParser:

    @classmethod
    @dec.measure_time
    def create_reports(cls, ci_folders: str, project: str, writer: pandas.ExcelWriter):
        """Write a report for each folder with rest results"""
        logger.info('Report file creation started')
        workbook = writer.book

        # Format 'Result' cells for passed and failed tests
        format_green = workbook.add_format({'bold': 1, 'font_color': 'green'})
        format_red = workbook.add_format({'bold': 1, 'font_color': 'red'})

        header_format = workbook.add_format(cfg.HEADER_FORMAT)

        # Walk through the daily folders and create a worksheet wor each one
        for folder in glob.glob(ci_folders):
            path = folder + '\\*\\*.trx'
            split_path = [item for item in folder.split('\\') if item]  # remove empty strings
            report_date = split_path[-1].split('_')[1]  # get only day number
            theme = split_path[-2]
            sheet_name = '{}_{}_{}'.format(project, theme[:4], report_date)
            header = cfg.TABLE_HEADER

            output = cls.iterate_through_files_in_folder_and_parse_content(path)

            tests_results = output[0]
            total_trx = output[1]
            failed_trx = output[2]

            Stats.create_brief_summary_for_theme(folder, total_trx, failed_trx)

            data_frame = pandas.DataFrame(columns=header)
            data_frame = data_frame.append(pandas.DataFrame(tests_results, columns=header), ignore_index=True)
            data_frame.to_excel(writer, sheet_name=sheet_name)

            worksheet = writer.sheets[sheet_name]

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

        logger.info('Report file created successfully')

    @classmethod
    def get_daily_folders_list(cls, path: str) -> list:
        daily_folders = []
        for folder in glob.glob(path + "\\*"):
            new_results = os.path.join(folder, datetime.today().strftime(cfg.DATETIME_FORMAT))
            days_from_now = 1
            # If there are no folders for the last three days - break
            while days_from_now != 3:
                if FileHelper.folder_has_trx_files(new_results):
                    daily_folders.append(new_results)
                    logger.info('Results folder found: ' + new_results)
                    break

                day_before = datetime.today() - timedelta(days=days_from_now)
                new_results = os.path.join(folder, day_before.strftime(cfg.DATETIME_FORMAT))
                days_from_now += 1

        return daily_folders

    @classmethod
    def iterate_through_files_in_folder_and_parse_content(cls, path_to_folder: str) -> (list, int, int):
        """Iterate through the files in specified folder"""
        total_trx = 0
        failed_trx = 0
        result_list = list()
        try:
            for file in [item for item in glob.glob(path_to_folder, recursive=True)]:
                total_trx += 1
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
                    error_message = TrxHelper.open_trx_read_error(file)
                    result = 'FAILED'
                    failed_trx += 1

                feature = [*[group, ff_name, database, browser, build, timing, total,
                             passed, failed, skipped, result], *error_message]

                result_list.append(feature)
                logger.debug('Get feature info: {}'.format(feature))

            logger.info('Parsing files in folder: {} finished'.format(path_to_folder))
        except Exception as e:
            logger.error(e)
        finally:
            return result_list, total_trx, failed_trx


if __name__ == "main":
    pass
