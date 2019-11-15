# -*- coding: utf-8 -*-
import parse_trx_results as parser
from log_helper import init_logger


summary_pattern = """------------ Theme: {}
Total tests  count: {}
Passed tests count: {}
Failed tests count: {}
Passed: {} %

"""

email_footer = """
Python-generated email with the CI test results spreadsheet.
If you want to unsubscribe, please, click |HERE| or just email to vhanich@elinext.com.
"""


logger = init_logger()


def create_brief_summary_for_theme(path_to_theme, total_trx, failed_trx):
    try:
        theme = path_to_theme.split('\\')[-4]
        logger.info("Started brief summary creation for {}".format(theme))

        passed_trx = total_trx-failed_trx
        if total_trx:
            passed_percent = round((passed_trx / total_trx), 2) * 100
            parser.brief_summary.append([theme, total_trx, passed_trx, failed_trx, passed_percent])
        else:
            logger.warning("Found {} test results for theme {}. Summary wasn't created".format(total_trx, theme))

    except Exception as e:
        logger.error(e)


def create_email_body():
    message = []
    try:
        for item in parser.brief_summary:
           message.append(summary_pattern.format(item[0], item[1], item[2], item[3], item[4]))
    except Exception as e:
        logger.warning("Can't create brief summary: " + e)
    finally:
        return "".join(message) + email_footer
