#!/usr/bin/env python3
import pickle

import matplotlib.pyplot as plt
import pandas as pd

from offline.core.utils import *


def load_settings():
    try:
        with open("settings.pickle", "rb") as f:
            return pickle.load(f)
    except IOError as e:
        print("no settings, starting from scartch")
        return {}


def plot_mean(labels):
    price = pd.DataFrame.from_csv("eval.csv")
    prices_label = [a for a in list(price) if a in labels]

    price = price[prices_label]
    price = pd.DataFrame(index=[pd.Timedelta(seconds=i) + pd.Timestamp('2012-05-01 00:00:00') for i in price.index],
                         data=price[prices_label].values, columns=prices_label)
    price = price.resample("60s").bfill().fillna(method="bfill")

    fig, ax1 = plt.subplots()
    for label in prices_label:
        plt.plot(price.index, price[label], )

    plt.legend(prices_label, loc='upper left')

    plt.show()


def plot_count(labels):
    e = pd.DataFrame.from_csv("eval.csv")
    print("%s" % list(e))
    data = [a for a in list(e) if a in labels]

    e = pd.DataFrame(index=[pd.Timedelta(seconds=i) + pd.Timestamp('2012-05-01 00:00:00') for i in e.index],
                     data=e[data].values,
                     columns=data)
    e1M = e.resample("60s").sum().fillna(0)

    # e1M["USER"].cumsum().plot()

    for d in data:
        plt.plot(e1M.index, e1M[d], )

    plt.legend(data, loc='upper left')
    plt.grid(True)
    plt.show()


def choose_settings(settings):
    io = ""
    e = pd.DataFrame.from_csv("eval.csv")
    e = sorted(list(e))
    message = ""
    while True:
        # os.system('clear')
        print("AVAILABLE ITEMS\n===============")
        for index, item in enumerate(e):
            print("[%d] %s" % (index, item))

        print("%s" % red(message))
        for index, item in enumerate(e):
            if item in settings:
                sys.stdout.write("[%s] %s\t"%(red(index),green(item)))
        sys.stdout.write("\n")

        choice = input()
        message = ""

        if choice == "go" or choice == "":
            break
        elif choice[0] == "r":
            # remove
            if e[int(choice[1:])] in settings:
                del settings[e[int(choice[1:])]]
            else:
                message = "column not selected"
        elif choice[0] == "a":
            # add
            settings[e[int(choice[1:])]] = True
    with open("settings.pickle", "wb") as f:
        pickle.dump(settings, f)
    return settings


settings = load_settings()
choose_settings(settings)

# plot_count(["REQUEST", "HIT.CDN", "HIT.VCDN"])
plot_mean(settings.keys())
