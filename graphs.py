import matplotlib.pyplot as plt
import pandas as pd
from collections import OrderedDict
from Helpers import decorators as dec


class Graphs:
    stats = {}

    @classmethod
    @dec.measure_time
    def create_magic_graphs(cls, data: dict):
        for theme_key in data.keys():
            data_set = {'date': [], 'total trx': [], 'passed trx': [], "passed %": []}
            data_theme = data[theme_key]

            if not data_theme:
                continue

            sorted_data = OrderedDict(sorted(data_theme.items()))
            for key in sorted_data.keys():
                data_set['date'].append(key)
                total = data_theme[key][0]
                passed = data_theme[key][1]
                percent = data_theme[key][-1]
                data_set['total trx'].append(int(total))
                data_set['passed trx'].append(int(passed))
                data_set['passed %'].append(float(percent))

            data_frame = pd.DataFrame(data_set)
            Graphs.stats[theme_key] = data_frame.to_html(index=False, border='1')

            plt.clf()
            plt.figure(figsize=(8, 6), frameon=False)
            plt.title(theme_key)

            ax = plt.gca()

            data_frame.plot(kind='line', x='date', y='total trx', ax=ax, color='blue', linestyle='dashed', marker='o',
                            markerfacecolor='black', markersize=5, label='Total tests')
            data_frame.plot(kind='bar', x='date', y='passed %', ax=ax, label='Passed %')

            # plot lines-markers (100 for percents)
            plt.axhline(y=100, color='red', linestyle='-')
            plt.subplots_adjust(bottom=0.3)
            plt.savefig("Output\\" + theme_key + '.png')


if __name__ == "main":
    pass
