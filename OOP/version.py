import glob
import traceback
import xml.etree.ElementTree as elTree

path = '\\\\testresultrepo.csiqa.local\\TestResults\\CI\\V8'


class Version:

    def __init__(self, path_to_ver):
        self.version = path_to_ver
        #self.projects_list = self.get_projects()

    def get_projects(self):
        ret = {}
        # for project_path in glob.glob(self.path_to_ver + '\\*', recursive=True):
        #     proj_name = project_path.split('\\')[-1]
        #     ret.update({proj_name: Project(project_path)})
        # return ret
        return [Project(project) for project in glob.glob(self.version + '\\*', recursive=True)]


class Project:
    def __init__(self, path_to_proj):
        self.project = path_to_proj
        #self.themes_list = self.get_themes()

    def get_themes(self):
        # ret = {}
        # for theme_path in glob.glob(self.path_to_proj + '\\*', recursive=True):
        #     theme_name = theme_path.split('\\')[-1]
        #     ret.update({theme_name: Theme(theme_path)})
        # return ret
        return [Theme(theme) for theme in glob.glob(self.project + '\\*', recursive=True)]


class Theme:
    def __init__(self, path_to_day):
        self.theme = path_to_day
        #self.days_list = self.get_days()

    def get_days(self):
        # ret = {}
        # for day_path in glob.glob(self.path_to_day + '\\*', recursive=True):
        #     day_name = day_path.split('\\')[-1]
        #     ret.update({day_name: Day(day_path)})
        # return ret
        return [Day(day) for day in glob.glob(self.theme + '\\*', recursive=True)]


class Day:
    stats_for_day = []
    features_list = []
    total_scenarios = 0
    passed = 0
    failed = 0
    percentage = 0.0

    def __init__(self, path_to_features):
        self.daily_folder = path_to_features
        self.stats_for_day = self.get_daily_stats()
        #self.features_list = self.get_features()


    def get_features(self):
        # ret = {}
        # for feature_path in glob.glob(self.path_to_features + '\\*\\*.trx', recursive=True):
        #     feature_name = feature_path.split('\\')[-1]
        #
        #     feature = Feature(feature_path)
        #     if feature.passed:
        #         self.passed += 1
        #     ret.update({feature_name: Feature(feature_path)})
        # return ret
        self.features_list = [Feature(feature) for feature in glob.glob(self.daily_folder + '\\*\\*.trx',
                                                                        recursive=True)]
        return self.features_list

    def get_amount_of_passed(self):
        passed_scen = 0
        for ff in glob.glob(self.daily_folder + '\\*\\*.trx', recursive=True):
            split_path_to_ff = ff.split('\\')
            trx_name = split_path_to_ff[-1]
            ff_info = [item.replace('.trx', '') for item in trx_name.split('_')]

            # Parts of feature info
            tail = ff_info[-1].split('-')
            results = tail[1:]
            failed = results[-2]
            if not failed:
                passed_scen += 1
        return passed_scen


    def get_daily_stats(self):
        self.total_scenarios = len(glob.glob(self.daily_folder + '\\*\\*.trx'))
        self.passed = self.get_amount_of_passed()
        self.failed = self.total_scenarios - self.passed
        if self.passed:
            self.percentage = "%.2f" % (self.passed / self.total_scenarios * 100)
        else:
            self.percentage = 0
        return [self.total_scenarios, self.passed, self.failed, self.percentage]

class Feature:
    feature = ''
    passed = True
    info = []

    def __init__(self, path_to_feature):
        self.feature = path_to_feature
        self.info = self.get_feature_info

    @property
    def get_feature_info(self) -> list:
        split_path_to_ff = self.feature.split('\\')
        trx_name = split_path_to_ff[-1]
        ff_info = [item.replace('.trx', '') for item in trx_name.split('_')]

        # Parts of feature info
        group = split_path_to_ff[-2].replace('CLTQACLIENT', '')
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
            error_message = self.open_trx_read_error()
            if error_message is None:
                error_message = ['-', '-', '-']
            result = 'FAILED'
            self.passed = False
        else:
            self.passed = True

        info_1 = [group, ff_name, database, browser, build, timing, total,
                  passed, failed, skipped, result]
        return [*info_1, *error_message]

    def open_trx_read_error(self) -> list:
        tree = elTree.parse(self.feature)
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
                    #for errorInfo in output:
                    #for errorInfo in std_out:
                        #error_list = [item for item in errorInfo.text.split('\n')]
                    error_list = [line for line in std_out.text.split('\n')]
                    if len(error_list) == 1:
                        # error_message = errorInfo.text
                        return [test_name, stack_trace.text[:50], message.text]

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
                                    break
                                step_with_error = error_list[line - i]

                            info = [test_name, step_with_error, error_list[line]]
                            return info


class Scenario:
    def __init__(self):
        pass

import json
v8 = Version(path)
for project in v8.get_projects():

    json_data = json.dumps(project.__dict__)
    print(json_data)
    for theme in project.get_themes():
        print(json.dumps(theme.__dict__))
        for day in theme.get_days():
            print(json.dumps(day.__dict__))
            for feature in day.get_features():
                print(json.dumps(feature.__dict__))


#projects = v8.projects_list


# debug = r'\\testresultrepo.csiqa.local\TestResults\CI\V8\FOUNDATION\Horizon\11_30_2019\CEP CM_2_CLTQACLIENT492\90.14-Package Approvals-PLM_Desktop_Horizon_Oracle_Chrome_B8.1.19334.1-91-57-56-0-1.trx'
# feature = Feature(debug)
# json_data = json.dumps(feature.__dict__)
# print(json_data)


