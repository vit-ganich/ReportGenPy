import os
from log_helper import init_logger


logger = init_logger()


def check_file_is_empty(file, size_limit=6000):
    if os.path.getsize(file) < size_limit:
        os.remove(file)
        logger.warning('Report file \'{}\' is empty, email was not sent'.format(file))
        raise FileNotFoundError
    else:
        logger.info('Report file \'{}\' is ready '.format(file))


if __name__ == "main":
    pass