from Helpers import config_reader as cfg
from graphs import Graphs
from datetime import datetime
from Helpers.log_helper import init_logger
from stats import Stats

logger = init_logger()


class MessageHelper:
    summary_pattern = """------------ Theme: {}
    Total tests  count: {}
    Passed tests count: {}
    Failed tests count: {}
    Passed: {} %

    """
    summary_pattern_html = """--> {}<br>
    Total tests  count: <b>{}</b><br>
    Passed tests count: <font color="green"><b>{}</b></font><br>
    Failed tests count: <font color="red"><b>{}</b></font><br>
    Passed: <b>{} %</b><br>
    <br>
    """

    email_footer_pattern = """
    Python-generated email with the CI test results spreadsheet.
    If you want to unsubscribe, please, email to vhanich@elinext.com.
    Happy {}!
    """
    email_footer_pattern_html = """<br>
    Python-generated email with the CI test results spreadsheet.<br>
    <i>If you want to unsubscribe, please, email to vhanich@elinext.com.</i><br>
    Happy {}!<br>
    """

    email_runs_history_pattern = """
    History (see graphs in the attachments):

    {}
    """
    email_runs_history_pattern_html = """------------<br>
    <b>CI runs history</b> <i>(see graphs in the attachments):</i><br>
    <br>
    {}<br>
    """

    @classmethod
    def create_email_body(cls) -> str:
        message = []
        history = ''
        footer = ''
        try:
            for item in Stats.stats_for_today:
                message.append(MessageHelper.summary_pattern_html.format(item[0], item[1],
                                                                         item[2], item[3], item[4]))
            raw_history = cls.create_runs_history()
            history = MessageHelper.email_runs_history_pattern_html.format(raw_history)
            footer = MessageHelper.email_footer_pattern_html.format(datetime.today().strftime('%A'))

        except Exception as e:
            logger.warning("Can't create brief summary: " + e)
        finally:
            bonus_info = "".join(message) + history + footer
            logger.info(bonus_info)
            return bonus_info

    @classmethod
    def create_runs_history(cls) -> str:
        history = []
        for key, value in Graphs.stats.items():
            history.append(key.capitalize())
            history.append(value)

        return "\n".join(history)

    @classmethod
    def get_debug_info(cls) -> str:
        """Read log file from end to start and get info of the last run"""
        data = []
        with open(cfg.data['log_file'], 'r') as fread:
            for line in reversed(list(fread)):
                data.append(line.rstrip())
                if "Program started" in line:
                    break
        return "\n".join(data[::-1])


if __name__ == "main":
    pass
