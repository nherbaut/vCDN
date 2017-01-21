#!/usr/bin/env python


import multiprocessing
import os
import sys
from multiprocessing.pool import ThreadPool

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..pricing.generator import price_slas
from ..time.slagen import get_forecast, discretize, chunk_series_as_sla

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/extar')


def best_price(forecast, pricer=price_slas, cilevel="fcmean"):
    ts = pd.Series(forecast[cilevel].values, index=pd.to_datetime(forecast["Index"].values))
    best_price = sys.float_info.max
    for windows in range(1, 11, 2):
        for centroids in range(1, 20, 2):
            tses = discretize(windows, centroids, ts=ts, df=forecast)
            slas = chunk_series_as_sla({1: tses})
            price = pricer([item for sublist in list(slas.values()) for item in sublist])
            if best_price > price:
                best_price = price

    return price


def perform_forecast_bench(folders, filter=lambda x: True if "daily" in x and not "forecast" in x else False):
    data_files = []
    for folder in folders:
        data_files += [os.path.join(folder, file) for file in os.listdir(folder) if list(filter(file))]

    pool = ThreadPool(multiprocessing.cpu_count() - 1)
    forecasts = pool.map(get_forecast, data_files)
    means = []
    for file, ts, df in forecasts:

        sla_vio_mean = len(df[((df["fc0"] - df["fcmean"]) > 0) == True]) * 100.0 / len(
            df[((df["fc0"] - df["fcmean"]) != 0) == True])
        sla_vio_fc80 = len(df[((df["fc0"] - df["fc80"]) > 0) == True]) * 100.0 / len(
            df[((df["fc0"] - df["fc80"]) != 0) == True])
        sla_vio_fc95 = len(df[((df["fc0"] - df["fc95"]) > 0) == True]) * 100.0 / len(
            df[((df["fc0"] - df["fc95"]) != 0) == True])

        edata = np.abs(np.subtract(df["fc0"], df["fcmean"]))
        mape = 100 * np.mean(np.divide((1.0 * np.abs(np.subtract(df["fc0"], df["fcmean"]))), df["fc0"]))
        edata = edata[edata > 0]
        q = 0
        for j in range(24 + 1, len(df["fc0"] - 24 - 1)):
            q += np.abs(df["fc0"][j] - df["fc0"][j - 24])
        RMSE = np.sqrt(np.mean(np.power(edata, 2)))
        mea = np.mean(edata)
        mase = mea / (1.0 / (len(df["fc0"]) - 24) * q)
        means.append({"MASE": mase, "MEA": mea, "MAPE": mape, "file": file, "RMSE": RMSE,
                      "sla_vio_mean": sla_vio_mean,
                      "sla_vio_fc80": sla_vio_fc80,
                      "sla_vio_fc95": sla_vio_fc95,
                      "price_fc95": best_price(df, cilevel="fc95"),
                      "price_fc80": best_price(df, cilevel="fc80"),
                      "price_fcmean": best_price(df, cilevel="fcmean"),

                      })

    return means


def plot_forecast_bench(means):
    def sort_by_name_and_mape(x):
        file = x["file"]
        mape = x["MAPE"]
        if "IX" in file:
            return 10 ** 10 + mape
        if "linx" in file:
            return 10 ** 15 + mape
        if "ecix" in file:
            return 10 ** 20 + mape
        else:
            return 10 ** 25 + mape

    fig, ax1 = plt.subplots()

    ax2 = ax1.twinx()

    # ax1.set_title('Forecast Accuracy over every dataset')
    ax1.set_ylabel('MAPE Metric')
    ax2.set_ylabel('MASE Metric')
    import pickle
    with open("means.pickle","w") as f:
        pickle.dump(means,f)
    exit(-2)

    index, mape, mase, file = list(zip(
        *[(index, x["MAPE"], x["MASE"], os.path.basename(x["file"]).split("daily")[0]) for index, x in
          enumerate(sorted(means,
                           # key=lambda x: os.path.basename(x["file"]).split("daily")[0]))])
                           key=sort_by_name_and_mape))]))

    ax1.set_xticks(np.arange(0, len(file) + 1, 1))

    ax1.set_xticklabels(np.array(file))
    ax1.set_xticklabels(ax1.xaxis.get_majorticklabels(), rotation=45, fontsize=9)

    ax1.bar(index, mape, width=0.5, color='b', label="MAPE")
    ax2.bar(np.array(index) + 0.5, mase, width=0.5, color='r', alpha=0.5, label="MASE")
    # ax2.plot(index, np.ones(len(index)), color="black", linewidth=1, label="Naive forecast threshold")
    ax1.set_xlim((0, len(file) + 1))
    ax2.set_ylim(0, np.max(mase) + 1)

    # ax.bar(mape_index, mape_data)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()

    plt.legend(h1 + h2, l1 + l2, loc='best', )
    ax1.set_title("Forecasts quality")

    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.savefig("forecast.svg")
    plt.show(block=True)

    fig, ax1 = plt.subplots()
    ax1.set_xticks(np.arange(0, len(file) + 1, 1))
    ax1.set_xticklabels(np.array(file))
    ax1.set_xticklabels(ax1.xaxis.get_majorticklabels(), rotation=45, fontsize=7)

    index, file, fcmean_score, fc80_score, fc95_score = list(zip(
        *[(index, os.path.basename(x["file"].split("daily")[0]), x["sla_vio_mean"], x["sla_vio_fc80"],
           x["sla_vio_fc95"],)
          for index, x in
          enumerate(sorted(means,
                           # key=lambda x: os.path.basename(x["file"]).split("daily")[0]))])
                           key=lambda x: -x["MAPE"]))]))

    ax1.bar(np.array(index), fcmean_score, width=0.3, color='r', label="Prediction", )
    ax1.bar(np.array(index) + 0.3, np.array(fc80_score) + 2, width=0.3, color='g', label="80% CI", )
    ax1.bar(np.array(index) + 0.3 + 0.3, np.array(fc95_score) + 1, width=0.3, color='b', label="95% CI", )
    ax1.set_title("SLA violations for Forecasts")
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.savefig("slas.svg")
    plt.show(block=True)

    fig, ax1 = plt.subplots()
    ax1.set_xticks(np.arange(0, len(file) + 1, 1))
    ax1.set_xticklabels(np.array(file))
    ax1.set_xticklabels(ax1.xaxis.get_majorticklabels(), rotation=45, fontsize=9)

    index, price_fc95, price_fc80, price_fcmean = np.array(
        [(index, x["price_fc95"], x["price_fc80"],
          x["price_fcmean"],)
         for index, x in
         enumerate(sorted(means,
                          # key=lambda x: os.path.basename(x["file"]).split("daily")[0]))])
                          key=lambda x: -x["MAPE"]))]).T

    nprice_95 = np.divide(price_fc95, price_fcmean) * 100
    nprice_80 = np.divide(price_fc80, price_fcmean) * 100
    # nprice_mean = np.divide(price_fcmean,price_fc95)*100


    # ax1.set_ylim(0, np.max(nprice_95))
    ax1.bar(index, nprice_95, width=0.5, color='b', label="95% CI price increase", )
    ax1.bar(index + 0.5, nprice_80, width=0.5, color='g', label="80% CI CI price increase", )

    ax1.set_title("Prices for Forecasts (% wrt 95% CI)")
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.savefig("prices.svg")
    plt.show(block=True)
