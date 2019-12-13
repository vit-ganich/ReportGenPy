import traceback
import pandas
from stats import Stats
from graphs import Graphs
from Helpers.log_helper import init_logger
from parse_trx_results import TrxParser
from postman import Postman
from Helpers import config_reader as cfg
from Helpers.file_helper import FileHelper


logger = init_logger()

try:
    logger.info("----------------Program started")

    if FileHelper.output_folder_exists():
        FileHelper.clear_output_folder()

    daily_folders = TrxParser.get_daily_folders_list(cfg.PATH)

    date = daily_folders[0].split('\\')[-1]
    report_file = '{}_{}.{}'.format(cfg.data['report_name'], date, cfg.data['report_extension'])
    writer = pandas.ExcelWriter(report_file, engine='xlsxwriter')

    for folder in daily_folders:
        project = folder.split('\\')[-3]
        TrxParser.create_reports(folder, project, writer)

    data = Stats.get_stats_for_all_time(cfg.PATH)
    Graphs.create_magic_graphs(data)
    writer.save()
    Postman.send_email(report_file_to_send=report_file)

    logger.info("----------------Program finished\n")
except Exception:
    Postman.send_email_debug(traceback.format_exc())
    print(traceback.format_exc())
