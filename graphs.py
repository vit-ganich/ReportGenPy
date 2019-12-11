import matplotlib.pyplot as plt
import pandas as pd
import statis
from collections import OrderedDict
import decorators as dec
import postman

stats = {}

@dec.measure_time
def do_magic(data):
    for theme_key in data.keys():
        data_set = {'date':[], 'total trx':[], 'passed trx':[], "passed %":[]}
        data_theme = data[theme_key]
        sorted_data = OrderedDict(sorted(data_theme.items()))
        for key in sorted_data.keys():
            #date_formatted = '-'.join(key.split('_')[:2])
            data_set['date'].append(key)
            total = data_theme[key][0]
            passed = data_theme[key][1]
            perc = data_theme[key][-1]
            data_set['total trx'].append(int(total))
            data_set['passed trx'].append(int(passed))
            data_set['passed %'].append(float(perc))
    
        data_frame = pd.DataFrame(data_set)
        stats[theme_key] = data_frame.to_string(index = False)
        plt.clf()
        plt.figure(figsize=(8,6), frameon=False)
        plt.title(theme_key)

        ax = plt.gca()

        data_frame.plot(kind='line', x='date', y='total trx', ax=ax, color='blue', linestyle='dashed', marker='o', markerfacecolor='black', markersize=5, label='Total tests')
        data_frame.plot(kind='bar', x='date', y='passed %', ax=ax, label='Passed %')

        # plot lines-markers
        plt.axhline(y=100, color='red', linestyle='-')

        if(theme_key == 'classic'):
            plt.axhline(y=120, color='green', linestyle='-.')
        else:
            plt.axhline(y=300, color='green', linestyle='-.')

        plt.subplots_adjust(bottom=0.3)
        plt.savefig(theme_key + '.png')


if __name__ == "main":
    pass
