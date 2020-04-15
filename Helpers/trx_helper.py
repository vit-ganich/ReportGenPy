import xml.etree.ElementTree as elTree
from Helpers.log_helper import init_logger

logger = init_logger()


class TrxHelper:
    @classmethod
    def open_trx_read_error(cls, file: str) -> list:
        logger.debug('Reading the TRX file with errors')
        tree = elTree.parse(file)
        root = tree.getroot()
        results = root.find('{http://microsoft.com/schemas/VisualStudio/TeamTest/2010}Results')

        for unitTesResult in results:
            if unitTesResult.attrib['outcome'] == 'Failed':
                test_name = unitTesResult.attrib['testName']
                for output in unitTesResult:
                    children = list(output)
                    std_out = children[0]
                    error_info = children[1]
                    message = list(error_info)[0]
                    stack_trace = list(error_info)[1]
                    error_list = [line for line in std_out.text.split('\n')]
                    # Sometimes there is only one line in StdOut
                    if len(error_list) == 1:
                        return [test_name, stack_trace.text[:50], message.text]
                    # Walk through the lines in StdOut
                    for line in range(len(error_list)):
                        # Find an error in scenario output
                        if '-> error:' in error_list[line]:
                            # Step with error usually located at the previous line before error message
                            step_with_error = error_list[line - 1]
                            if len(error_list) == 1:
                                break
                            # But sometimes not the previous, so we search in upper lines
                            for i in range(2, 40):
                                # Scenarios always start with Gherkin keywords
                                if step_with_error.startswith(('Given', 'When', 'Then', 'And')):
                                    logger.debug('Step with error: {}'.format(step_with_error))
                                    break
                                step_with_error = error_list[line - i]

                            info = [test_name, step_with_error, error_list[line]]
                            return info


if __name__ == "main":
    pass
