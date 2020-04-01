import glob
import traceback
from Helpers.log_helper import init_logger
from datetime import datetime
import json

logger = init_logger()


class Stats:
    stats_for_today = []
    stats_for_all_time = {}

    @classmethod
    def get_stats_for_all_time(cls, path) -> dict:
        days_folders = [folder for folder in glob.glob(path + '\\*\\*', recursive=True)]
        for folder in days_folders:
            # if 'INDUSTRY SOLUTIONS' in folder:
            #     continue
            cls.iterate_through_files_in_folder_and_get_stats(folder)

        cls.save_stats_to_json()

        return cls.stats_for_all_time

    @classmethod
    def iterate_through_files_in_folder_and_get_stats(cls, path_to_folder: str):
        """Iterate through the files in specified folder and get a brief stats"""
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
        cls.create_stats_for_all_time(path_to_folder, total_trx, failed_trx)

    @classmethod
    def create_stats_for_all_time(cls, path_to_proj: str, total_trx: int, failed_trx: int):
        splitted_path_to_file = path_to_proj.split('\\')
        theme = '_'.join(splitted_path_to_file[-3:-1]).lower()
        logger.info("Get stats for all time for theme: {}".format(theme))
        raw_date = splitted_path_to_file[-1]
        datetime_obj = datetime.strptime(raw_date, '%m_%d_%Y')
        date = datetime_obj.strftime('%m %d %y')
        passed_trx = total_trx - failed_trx
        if total_trx:
            passed_percent = "%.2f" % ((passed_trx / total_trx) * 100)
            info = [total_trx, passed_trx, failed_trx, passed_percent]

            if theme not in cls.stats_for_all_time.keys():
                cls.stats_for_all_time[theme] = {date: info}
            else:
                cls.stats_for_all_time[theme].update({date: info})
        else:
            logger.warning("Found {} test results for theme {}. Summary wasn't created".format(total_trx, theme))

    @classmethod
    def create_brief_summary_for_theme(cls, path_to_theme: str, total_trx: int, failed_trx: int):
        try:
            theme = ' '.join(path_to_theme.split('\\')[-3:])
            logger.info("Started brief summary creation for {}".format(theme))

            passed_trx = total_trx - failed_trx
            if total_trx:
                passed_percent = "%.2f" % ((passed_trx / total_trx) * 100)
                cls.stats_for_today.append([theme, total_trx, passed_trx, failed_trx, passed_percent])
            else:
                logger.warning("Found {} test results for theme {}. Summary wasn't created".format(total_trx, theme))

        except Exception:
            logger.error(traceback.format_exc())

    @classmethod
    def save_stats_to_json(cls):
        file_name = "Output\\statistics.json"
        data = json.dumps(Stats.stats_for_all_time, sort_keys=True, indent=4)
        with open(file_name, 'w') as file:
            file.write(data)


if __name__ == "main":
    pass
