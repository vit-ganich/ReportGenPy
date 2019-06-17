import xml.etree.ElementTree as elTree
import re


def read_error(file: str) -> list:
    """Open TRX file and read error messages"""
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
                                    break
                                step_with_error = error_list[line - i]
                            return [extract_scenario_num(test_name), step_with_error, error_list[line]]


def extract_scenario_num(text: str) -> str:
    """Get only scenario number without long name"""
    match = re.search(r'\d\d*_*\d\d*_*\d\d*_?\d*\d*', text)
    if match:
        return match.group().split('_')[-1]
    else:
        return text
    

if __name__ == 'main':
    pass
