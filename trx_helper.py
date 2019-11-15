import xml.etree.ElementTree as elTree
from log_helper import init_logger


logger = init_logger()


def open_trx_read_error(file: str) -> list:
    logger.debug('Reading the TRX file with errors')
    tree = elTree.parse(file)
    root = tree.getroot()
    results = root.find('{http://microsoft.com/schemas/VisualStudio/TeamTest/2010}Results')

    for unitTesResult in results:
        if unitTesResult.attrib['outcome'] == 'Failed':
            test_name = unitTesResult.attrib['testName']
            for output in unitTesResult:
                for errorInfo in output:
                    error_list = [item for item in errorInfo.text.split('\n')]
                    for line in range(len(error_list)):
                        # Find an error in scenario output
                        if '-> error:' in error_list[line]:
                            # Step with error usually located at the previous line before error message
                            step_with_error = error_list[line - 1]
                            # But sometimes not the previous, so we search in upper lines
                            for i in range(2, 40):
                                # Scenarios always start with Gherkin keywords
                                if step_with_error.startswith(('Given', 'When', 'Then', 'And')):
                                    logger.debug('Step with error: {}'.format(step_with_error))
                                    break
                                step_with_error = error_list[line - i]
                            return [test_name, step_with_error, error_list[line]]
