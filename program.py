import parse_trx_results as parser
import postman
import traceback
from log_helper import init_logger


logger = init_logger()

try:
    logger.info("----------------Program started")
    parser.create_reports()
    postman.send_email()
    logger.info("----------------Program finished")
except Exception:
    postman.send_email_debug(traceback.format_exc())