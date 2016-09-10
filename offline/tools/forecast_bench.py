import os
from ..time.slagen import get_forecast
import numpy as np
DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')


def perform_forecast_bench(folder):
    data_files = [os.path.join(folder,file) for file in os.listdir(folder)]
    means=[]
    for file in data_files :
        if "daily" in file and not "forecast" in file:
            ts, df=get_forecast(file, force_refresh=True)
            edata=np.abs(np.divide(np.subtract(df["fc0"],df["fcmean"]),df["fc0"]))
            edata=edata[edata>0]
            e=100*np.mean(edata[:-1])
            means.append(e)

    for mean in sorted(means):
        print("%lf",mean)


    pass


if "__main__" == __name__:
    perform_forecast_bench(DATA_FOLDER )

