import logging
import config_reader as cfg


def init_logger():
    log = logging.getLogger('logger')
    log.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(cfg.LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    if log.hasHandlers():
        log.handlers.clear()
    log.addHandler(file_handler)

    return log


if __name__ == "main":
    pass
