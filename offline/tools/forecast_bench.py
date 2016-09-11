#!/usr/bin/env python
import multiprocessing
import os
from multiprocessing.pool import Pool

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
        mea = np.mean(edata)
        mase = mea / (1.0 / (len(df["fc0"]) - 24) * q)
        means.append((mase, mea, mape, file))
        print("%s:\t%lf\t%lf\t%lf" % (file, mase, mea, mape,))

    for mean in sorted(means):
        print("%s:\t%lf\t%lf\t%lf" % (mean[3], mean[0], mean[1], mean[2]))

    pass
