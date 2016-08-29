#!/usr/bin/env python
# Generate SLAS from a forecast
import argparse
import datetime
import locale
import os
import subprocess

import pandas as pd

from ..core.sla import Sla
from ..time.SLA3D import get_tse, chunk_serie_as_sla
from ..time.persistence import session

TIME_PATH = os.path.dirname(os.path.realpath(__file__))


def get_forecast_from_date(df):
    dff = df["fcmean"] - df["fc0"]
    return df["Index"].values[-df.index[len(df) - len(dff[dff == 0])]]


def fill_db_with_sla(tenant, file=None, windows=5, centroids=5, **kwargs):
    '''

    :param file: the file to read the data from
    :param windows: the size of the window for smoothing
    :param centroids: the number of threshold value to detec
    :param random: if True, new random data will be generated
    :return: a tuple containing :
              ts: the generated time serie and its forecast, as reccorded in the table
              date_start: the date of the first observation for the serie
              date_start_forecast: the date of the first forecast
              date_end_forecast: the date of the last forecast
    '''
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')
    if file is None:
        subprocess.call(["%s/compute_forecast.R" % TIME_PATH, "-o", "output.csv", "-r"], cwd=TIME_PATH,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'))
    else:
        subprocess.call(["%s/compute_forecast.R" % TIME_PATH, "-i", "%s" % file, "-o", "output.csv"], cwd=TIME_PATH,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'))

    df = pd.read_csv(os.path.join(TIME_PATH, "output.csv"))

    ts = pd.Series(data=df["fcmean"].values,
                   index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                  axis=1).values)
    ts_forecasts = ts[get_forecast_from_date(df):]
    tse = get_tse(ts_forecasts, windows, centroids)

    for sla in chunk_serie_as_sla(tse):
        sla_instance = Sla(start_date=pd.to_datetime(sla.index[0]), end_date=pd.to_datetime(sla.index[-1]),
                           bandwidth=sla[0],
                           tenant_id=tenant.id,
                           start_nodes=kwargs.get("start_nodes", []),
                           cdn_nodes=kwargs.get("cdn_nodes", []),
                           substrate=kwargs.get("substrate",None),
                           delay=kwargs.get("delay", 50)
                           )

        session.add(sla_instance)



    return (ts, ts.index[0], get_forecast_from_date(df), ts.index[-1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='1 iteration for solver')
    parser.add_argument('--file', "-f", default="forecast.csv", type=str)
    parser.add_argument('--windows', "-w", default=5, type=int)
    parser.add_argument('--centroids', "-c", default=5, type=int)
    args = parser.parse_args()
    fill_db_with_sla(file=args.file, windows=args.windows, centroids=args.centroids)
