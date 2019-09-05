import logging
import config_reader as cfg


def init_logger():
    log = logging.getLogger('logger')
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler(cfg.LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    if log.hasHandlers():
        log.handlers.clear()
    log.addHandler(fh)

    return log


if __name__ == "main":
    pass
