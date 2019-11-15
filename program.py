import parse_trx_results as parser
import postman
from log_helper import init_logger


logger = init_logger()

logger.info("----------------Program started")

parser.create_reports()
postman.send_email()

logger.info("----------------Program finished")