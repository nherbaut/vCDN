#!/usr/bin/env python
import multiprocessing
import os
from multiprocessing.pool import Pool

import matplotlib.pyplot as plt
import numpy as np

from ..time.slagen import get_forecast

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/extar')


def perform_forecast_bench(folder):
    data_files = [os.path.join(folder, file) for file in os.listdir(folder) if
                  "daily" in file and not "forecast" in file]

    pool = Pool(multiprocessing.cpu_count() - 1)
    forecasts = pool.map(get_forecast, data_files)
    means = []
    for file, ts, df in forecasts:

        edata = np.abs(np.subtract(df["fc0"], df["fcmean"]))
        mape = 100 * np.mean(np.divide(np.abs(np.subtract(df["fc0"], df["fcmean"])), df["fc0"]))
        edata = edata[edata > 0]
        q = 0
        for j in range(24 + 1, len(df["fc0"] - 24 - 1)):
            q += np.abs(df["fc0"][j] - df["fc0"][j - 24])
        RMSE = np.sqrt(np.mean(np.power(edata, 2)))
        mea = np.mean(edata)
        mase = mea / (1.0 / (len(df["fc0"]) - 24) * q)
        means.append({"MASE": mase, "MEA": mea, "MAPE": mape, "file": file, "RMSE": RMSE})

    return means


def plot_forecast_bench(means):
    fig, ax = plt.subplots()
    ax2 = ax.twinx()

    ax.set_title('Forecast Accuracy over every dataset')
    ax.set_ylabel('% MAPE accuracy')
    ax2.set_ylabel('MASE LEVEL')
    mape_index, mape_data, RMSE = zip(
        *[(index, x["MAPE"], x["RMSE"]) for index, x in
          enumerate(sorted(means, key=lambda x: x["MAPE"]))])

    mase_index, mase_data, RMSE = zip(
        *[(index, x["MASE"], x["RMSE"]) for index, x in
          enumerate(sorted(means, key=lambda x: x["MASE"]))])

    ax.bar(mape_index, mape_data, width=1, color='b', align='center', label="MAPE")
    ax2.bar(np.array(mase_index), mase_data, width=1, color='r', align='center', alpha=0.5, label="MASE")
    ax2.plot(mape_index, np.ones(len(mape_index)), color="black", linewidth=3, label="Naive forecast threshold")
    ax.set_xlim((0, len(mape_index) + 1))
    ax2.set_ylim(0, 3)

    # ax.bar(mape_index, mape_data)
    ax.legend()
    ax2.legend()
    plt.show()
