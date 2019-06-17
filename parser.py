import glob
import xml_reader


def parse(path_to_folder: str) -> list:
    """Iterate through the files in specified folder"""
    result_list = list()
    for file in [item for item in glob.glob(path_to_folder, recursive=True)]:
        file_name = file.split('\\')[-2:]
        ff_info = [item.replace('.trx', '') for item in file_name[1].split('_')]
        # Parts of feature info
        group = file_name[0].replace('CLTQACLIENT', '')
        ff_name = '_'.join(ff_info[:-5])
        database = ff_info[-3]
        browser = ff_info[-2]
        tail = ff_info[-1].split('-')
        build = tail[0]
        results = tail[1:]
        timing = results[0]
        total = results[-4]
        passed = results[-3]
        failed = results[-2]
        skipped = results[-1]
        error_message = ['-', '-', '-']
        result = 'PASSED'
        if int(failed):
            error_message = xml_reader.read_error(file)
            result = 'FAILED'
        feature = [*[group, ff_name, database, browser, build, timing, total,
                   passed, failed, skipped, result], *error_message]
        result_list.append(feature)
    return result_list