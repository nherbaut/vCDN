#!/usr/bin/env python
# Generate SLAS from a forecast
import argparse
import locale
import subprocess

import namesgenerator
import pandas as pd
from SLA3D import *
from persistence import *
from sqlalchemy import create_engine


def get_forecast_from_date(df):
    dff = df["fcmean"] - df["fc0"]
    return df["Index"].values[-df.index[len(df) - len(dff[dff == 0])]]


def fill_db_with_sla(file="forecast.csv", windows="5", centroids="5", random=True):
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
    if random:
        subprocess.call(["Rscript", "main_random.R"])
    else:
        subprocess.call(["Rscript", "main.R"])

    df = pd.read_csv(file)
    ts = pd.Series(data=df["fcmean"].values,
                   index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                  axis=1).values)
    ts_forecasts = ts[get_forecast_from_date(df):]
    tse = get_tse(ts_forecasts, windows, centroids)
    tenant = Tenant(name=namesgenerator.get_random_name(), slas=[])
    engine = create_engine('sqlite:///example.db', echo=True)
    session.add(tenant)
    for sla in chunk_serie_as_sla(tse):
        sla_isntance = SLA(start=pd.to_datetime(sla.index[0]), end=pd.to_datetime(sla.index[-1]), bandwidth=sla[0],
                           tenant=tenant)
        session.add(sla_isntance)

    session.commit()
    return (ts,ts.index[O],get_forecast_from_date(df),ts.index[-1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='1 iteration for solver')
    parser.add_argument('--file', "-f", default="forecast.csv", type=str)
    parser.add_argument('--windows', "-w", default=5, type=int)
    parser.add_argument('--centroids', "-c", default=5, type=int)
    args = parser.parse_args()
    fill_db_with_sla(file=args.file, windows=args.windows, centroids=args.centroids)
