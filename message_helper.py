# -*- coding: utf-8 -*-
import parse_trx_results as parser
import config_reader as cfg
import traceback
import graphs
from datetime import datetime
from log_helper import init_logger


summary_pattern = """------------ Theme: {}
Total tests  count: {}
Passed tests count: {}
Failed tests count: {}
Passed: {} %

"""

summary_pattern_html = """------------ Theme: <b>{}</b><br>
Total tests  count: <b>{}</b><br>
Passed tests count: <font color="green"><b>{}</b></font><br>
Failed tests count: <font color="red"><b>{}</b></font><br>
Passed: <b>{} %</b><br>
"""

email_footer = """
Python-generated email with the CI test results spreadsheet.
If you want to unsubscribe, please, email to vhanich@elinext.com.
Happy {}!
""".format(datetime.today().strftime('%A'))

email_footer_html = """<br>
<i>Python-generated email with the CI test results spreadsheet.</i><br>
<i>If you want to unsubscribe, please, email to vhanich@elinext.com.</i><br>
Happy {}!<br>
""".format(datetime.today().strftime('%A'))

email_runs_history = """
P.S. Some additional statistics through CI runs (DEMO):
{}
"""


logger = init_logger()


def create_brief_summary_for_theme(path_to_theme, total_trx, failed_trx):
    try:
        theme = path_to_theme.split('\\')[-4]
        logger.info("Started brief summary creation for {}".format(theme))

        passed_trx = total_trx-failed_trx
        if total_trx:
            passed_percent = "%.2f" % ((passed_trx / total_trx) * 100)
            parser.brief_summary.append([theme, total_trx, passed_trx, failed_trx, passed_percent])
        else:
            logger.warning("Found {} test results for theme {}. Summary wasn't created".format(total_trx, theme))

    except Exception:
        logger.error(traceback.format_exc())


def create_email_body():
    message = []
    try:
        for item in parser.brief_summary:
           message.append(summary_pattern.format(item[0], item[1], item[2], item[3], item[4]))
           history = email_runs_history.format(create_runs_history())
    except Exception as e:
        logger.warning("Can't create brief summary: " + e)
    finally:
        summary = "".join(message) + email_footer + history
        logger.info(summary)
        return summary


def create_runs_history():
    history = []
    for key, value in graphs.stats.items():
       history.append(key)
       history.append(value)
    return "\n".join(history)

def get_debug_info():
    """Read log file from end to start and get info of the last run"""
    data = []
    with open(cfg.data['log_file'], 'r') as fread:
        for line in reversed(list(fread)):
            data.append(line.rstrip())
            if "Program started" in line:
                break
    return "\n".join(data[::-1])
