import os
from ..time.slagen import get_forecast
import numpy as np
DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')


def perform_forecast_bench(folder):
    data_files = [os.path.join(folder,file) for file in os.listdir(folder)]

    for file in data_files :
        ts, df=get_forecast(file, force_refresh=True)
        np.subtract(df["fc0"],df["fcmean"])




    pass


if "__main__" == __name__:
    perform_forecast_bench(DATA_FOLDER )

