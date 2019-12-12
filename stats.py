import glob
import os
import message_helper as msg_helper
import config_reader as cfg
from datetime import datetime, timedelta
from log_helper import init_logger
from datetime import datetime
import json
import decorators as dec

logger = init_logger()
final_set = {'classic':{}, 'horizon':{}}


def get_stats_for_all_time() -> dict: 
    days_folders = [folder for folder in glob.glob(cfg.PATH + "\\*", recursive=True)]
    for folder in days_folders:
        iterate_through_files_in_folder_and_parse_content(folder)

    save_stats_to_json()

    return final_set


def iterate_through_files_in_folder_and_parse_content(path_to_folder: str) -> list:
    """Iterate through the files in specified folder"""
    total_trx = 0
    failed_trx = 0
    for file in [item for item in glob.glob(path_to_folder + "\\*\\*.trx", recursive=True)]:
        total_trx += 1
        file_name = file.split('\\')[-2:]
        ff_info = [item.replace('.trx', '') for item in file_name[1].split('_')]
        # Parts of feature info
        tail = ff_info[-1].split('-')
        results = tail[1:]
        failed = results[-2]
        if int(failed):
            failed_trx += 1
    create_stats_for_day(path_to_folder, total_trx, failed_trx)

def create_stats_for_day(path_to_theme, total_trx, failed_trx):
        splitted_path_to_file = path_to_theme.split('\\')
        theme = splitted_path_to_file[-2].lower()
        raw_date = splitted_path_to_file[-1]
        datetime_obj = datetime.strptime(raw_date, '%m_%d_%Y')
        date = datetime_obj.strftime('%m %d %y')
        passed_trx = total_trx-failed_trx
        if total_trx:
            passed_percent = "%.2f" % ((passed_trx / total_trx) * 100)
            final_set[theme].update({date:[total_trx, passed_trx, failed_trx, passed_percent]})
        else:
            logger.warning("Found {} test results for theme {}. Summary wasn't created".format(total_trx, theme))


def save_stats_to_json(file_name="statistics.json"):
    data = json.dumps(final_set,sort_keys=True, indent=4)
    with open(file_name, 'w') as file:
        file.write(data)
    

if __name__ == "main":
    pass