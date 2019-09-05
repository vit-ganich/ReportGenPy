import json
from datetime import datetime


with open('config.json') as config_file:
    data = json.load(config_file)

PATH = data['path_to_test_results']
#PATH = data['path_debug']
DATETIME_FORMAT = data['datetime_format']
REPORT_FILE = '{}_{}.{}'.format(data['report_name'],
                                datetime.today().strftime(DATETIME_FORMAT),
                                data['report_extension'])
LOG_FILE = data["log_file"]
HEADER_FORMAT = data["header_format"]
TABLE_HEADER = data["table_header"]


if __name__ == "main":
    pass
