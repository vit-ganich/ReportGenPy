import os
import glob
from fnmatch import fnmatch
from Helpers.log_helper import init_logger

logger = init_logger()


class FileHelper:

    @classmethod
    def check_file_is_empty(cls, file: str, size_limit=6000):
        if os.path.getsize(file) < size_limit:
            os.remove(file)
            logger.warning('Report file \'{}\' is empty, email was not sent'.format(file))
            raise FileNotFoundError
        else:
            logger.info('Report file \'{}\' is ready '.format(file))

    @classmethod
    def folder_has_trx_files(cls, folder):
        if not os.path.exists(folder):
            return False
        for path, subdirs, files in os.walk(folder):
            for name in files:
                if fnmatch(name, '*trx'):
                    logger.info('Results folder found: ' + folder)
                    return True
        return False

    @classmethod
    def clear_output_folder(cls, folder='Output'):
        try:
            files = glob.glob(folder + '\\*')
            for f in files:
                os.remove(f)
        except FileNotFoundError:
            pass


if __name__ == "main":
    pass
