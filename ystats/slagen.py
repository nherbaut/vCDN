#!/usr/bin/env python
# Generate SLAS from a forecast
import argparse
import sqlite3
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from persistence import *
import subprocess
import namesgenerator


import locale
from SLA3D import *

locale.setlocale(locale.LC_ALL, 'en_US.utf8')
subprocess.call(["Rscript","main_random.R"])
def get_forecast_from_date(df):
    dff = df["fcmean"] - df["fc0"]
    return df["Index"].values[-df.index[len(df) - len(dff[dff == 0])]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='1 iteration for solver')
    parser.add_argument('--file', "-f", default="forecast.csv", type=str)
    parser.add_argument('--windows', "-w", default=5, type=int)
    parser.add_argument('--centroids', "-c", default=5, type=int)
    parser.add_argument('--plot', dest="plot", action="store_true")
    args = parser.parse_args()
    df = pd.read_csv(args.file)
    ts = pd.Series(data=df["fcmean"].values,
                   index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                  axis=1).values)
    ts_forecasts = ts[get_forecast_from_date(df):]
    tse = get_tse(ts_forecasts, args.windows, args.centroids)
    tenant = Tenant(name=namesgenerator.get_random_name(),slas=[])
    engine = create_engine('sqlite:///example.db', echo=True)
    session.add(tenant )
    for sla in chunk_serie_as_sla(tse):
        sla_isntance=SLA(start=pd.to_datetime(sla.index[0]), end=pd.to_datetime(sla.index[-1]), bandwidth=sla[0], tenant=tenant)
        session.add(sla_isntance)

    session.commit()
