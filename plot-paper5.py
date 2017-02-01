#!/usr/bin/env python3
import collections
import os
import pickle

import matplotlib.dates as dates
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

myFmt = mdates.DateFormatter('%S.%f')

import numpy as np
import pandas as pd

from offline.core.utils import *

try:
    def dd():
        return {}


    def load_settings():
        try:
            with open("settings.pickle", "rb") as f:
                return pickle.load(f)
        except IOError as e:
            print("no settings, starting from scartch")

            return collections.defaultdict(dd)


    def plot_mean(settings):
        labels = list(settings["columns"].keys())
        price = pd.DataFrame.from_csv("eval.csv")
        prices_label = [a for a in list(price) if a in labels]

        price = price[prices_label]
        price = pd.DataFrame(index=[pd.Timedelta(seconds=i) + pd.Timestamp('2012-05-01 00:00:00') for i in price.index],
                             data=price[prices_label].values, columns=prices_label)
        price = price.resample(settings["sampling"]).mean().fillna(method="bfill").dropna()
        price = price[:-settings["trim"]]

        fig, ax1 = plt.subplots()
        for label in prices_label:
            ax1.plot(price.index, price[label], )

        if "ylim" not in settings:
            ax1.set_ylim([0, np.max(price[labels].values) * 1.1])
        else:
            amin, amax = settings["ylim"]
            ax1.set_ylim([amin, amax])


        ax1.xaxis.set_major_formatter(dates.DateFormatter('%M'))
        ax1.legend(prices_label, loc='best')
        ax1.set_xlabel(settings["xlabel"])
        ax1.set_ylabel(settings["ylabel"])
        ax1.grid(True)

        if "file_name" in settings:
            plt.savefig(settings["file_name"], transparent=False, dpi=300)
        plt.show()


    def plot_count(settings):
        labels = list(settings["columns"].keys())
        e = pd.DataFrame.from_csv("eval.csv")

        data = [a for a in list(e) if a in labels]

        e = pd.DataFrame(index=[pd.Timedelta(seconds=i) + pd.Timestamp('2012-05-01 00:00:00') for i in e.index],
                         data=e[data].values,
                         columns=data)
        eval_resampled = e.resample(settings["sampling"]).sum().fillna(0)
        eval_resampled = eval_resampled[:-settings["trim"]]

        # e1_m["USER"].cumsum().plot()

        fig, ax1 = plt.subplots()
        for d in data:
            ax1.plot(eval_resampled.index, eval_resampled[d], )

        if "ylim" not in settings:
            ax1.set_ylim([np.min(eval_resampled[labels].values), np.max(eval_resampled[labels].values) * 1.1])
        else:
            amin, amax = settings["ylim"]
            ax1.set_ylim([amin, amax])

        ax1.xaxis.set_major_formatter(dates.DateFormatter('%M'))
        ax1.set_xlabel(settings["xlabel"])
        ax1.set_ylabel(settings["ylabel"])
        ax1.legend(data, loc='best')

        ax1.grid(True)
        plt.show()


    def choose_settings(settings):
        io = ""
        e = pd.DataFrame.from_csv("eval.csv")
        e = sorted(list(e))
        message = ""
        while True:
            os.system('clear')
            print("AVAILABLE ITEMS\n===============")
            for index, item in enumerate(e):
                print("[%d] %s" % (index, item))

            print("%s" % red(message))
            sys.stdout.write("mode: %s\t" % yellow(settings["mode"]))
            sys.stdout.write("sampling: %s\n" % yellow(settings["sampling"]))
            for index, item in enumerate(e):
                if item in settings["columns"]:
                    sys.stdout.write("[%s] %s\t" % (red(index), green(item)))
            sys.stdout.write("\n")

            choice = input()
            message = ""

            if choice == "go" or choice == "":
                break
            elif choice[0] == "r":
                # remove
                if e[int(choice[1:])] in settings["columns"]:
                    del settings["columns"][e[int(choice[1:])]]
                else:
                    message = "column not selected"
            elif choice[0] == "a":
                # add
                try:
                    settings["columns"][e[int(choice[1:])]] = True
                except ValueError:
                    for column in e:
                        if choice[1:] in column:
                            settings["columns"][column] = True



            elif choice[0] == "m":
                if choice[1] == "v":
                    settings["mode"] = "value"
                elif choice[1] == "a":
                    settings["mode"] = "average"
                else:
                    print(red("no such mode, quitting"))
                    exit(-1)
            elif choice[0] == "s":
                settings["sampling"] = choice[1:]
            elif choice == "cc":
                settings["columns"].clear()
            elif choice[0] == "X":
                settings["xlabel"] = choice[1:]
            elif choice[0] == "Y":
                settings["ylabel"] = choice[1:]
            elif choice[0:4] == "trim":
                settings["trim"] = int(choice[4:])
            elif choice[0] == "e":
                file_name = choice[2:]
                settings["file_name"] = file_name
            elif choice[0:4] == "ylim":
                if choice[5:] == "off":
                    del settings["ylim"]
                else:
                    x, y = choice[5:].split(" ")
                    settings["ylim"] = (float(x), float(y))

            elif choice == "help":
                print(
                    "mv = value, ma = average, a1 = add 1 to the list, r1 = remove 1 from the list, s 60s = sampling of 60 s. Press return to proceed")
                input()

        with open("settings.pickle", "wb") as f:
            pickle.dump(settings, f)
        return settings


    settings = load_settings()

    while True:
        choose_settings(settings)

        # plot_count(["REQUEST", "HIT.CDN", "HIT.VCDN"])
        if settings["mode"] == "average":
            plot_mean(settings)
        elif settings["mode"] == "value":
            plot_count(settings)
        else:
            print(red("please specify mode (eg. mv for value,  ma for average (current: %s" % settings["mode"]))


except KeyboardInterrupt as e:
    print("thanks bye")
