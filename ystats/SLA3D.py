    #!/usr/bin/env python
# turn test.csv to proper time serie

from __future__ import print_function

import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import sklearn.cluster
from mpl_toolkits.mplot3d import Axes3D
# from mpl_toolkits.mplot3d import Axes3D
matplotlib.style.use('ggplot')


def chunk_serie_as_sla(serie):
    res = []
    # as long as we have observations >0
    while not serie.empty:
        min = np.min(serie)
        for i in np.split(serie.index, np.where(np.diff(serie.index) / pd.Timedelta('1 H') != 1)[0] + 1):
            res.append(pd.Series(min, index=i))
        serie = serie - min
        serie = serie[serie > 0]
    return res


def price_slas(slas,ratio=21):
    prices = []
    cumtime = pd.Timedelta(0)
    for sla in slas:
        prices.append(price_sla(sla[0], sla.index[0], sla.index[-1],ratio=ratio))
        cumtime += (sla.index[-1] - sla.index[0])

    return sum(prices)


def price_sla(bw, date_start, date_end,ratio=21):

    hours = (date_end - date_start).value / (10 ** 9 * 3600.0)
    if hours == 0:
        print("what?")
        return 0
    f = lambda x: ratio if x > 24  else  (24 - x) / (x + 24) * (100 - ratio) + ratio
    price = bw * f(hours) * hours
    # print("%ld$ for %lf from %d H" % (price, bw, hours))
    return price


def get_tse(tsr, win, ncentroids=3):
    # tse=tsr.resample("%dH"%win).max().bfill()
    # tse=tse.rolling(window=win,center=True).max()
    # tse=tse.resample("1H").max().bfill()
    offset = pd.tseries.offsets.Hour(win)
    tsrr = tsr.resample("1H").bfill()
    tse = pd.Series(index=tsrr.index)
    start = tsr.index[0]
    end = tsr.index[-1]
    for i in range(0, int((end - start) / offset)):
        range_max = np.max(tsrr[(start + i * offset):(start + (i + 1) * offset)].values)
        tse[(start + i * offset):(start + (i + 1) * offset)] = range_max
    tse[(start + (i + 1) * offset):end] = np.max(tsrr[(start + (i + 1) * offset):end].values)
    fit = sklearn.cluster.KMeans(ncentroids).fit_predict(tse.values.reshape(-1, 1))
    for i in range(0, ncentroids):
        tse[fit == i] = max(tse.values * (fit == i))
    return tse


def get_3D_plot(ax3D,ratio=21,color="#ff0000"):
    # read data
    df = pd.read_csv("test2.csv", names=["time", "values"])
    # convert time column to proper time
    ts = pd.Series(data=df["values"].values,
                   index=df.apply(lambda row: datetime.datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S'),
                                  axis=1).values)
    # tsr=ts.resample("1H").max().ffill()
    tsr = ts
    MAX_WIN = 15
    MAX_CENTROID = 15
    X, Y = np.meshgrid(np.arange(2, MAX_WIN,2), np.arange(2, MAX_CENTROID,2))
    Z = np.array([price_slas(chunk_serie_as_sla(get_tse(tsr, x, y)),ratio=ratio) for (x, y) in zip(X.ravel(), Y.ravel())]).reshape(Y.shape)
    Z=Z/np.min(Z)*100


    surf = ax3D.plot_wireframe(X, Y, Z,color=color)


    return surf


if __name__ == "__main__":

    domain=np.arange(1,100,0.5)
    for key,i in enumerate(domain):
        fig = plt.figure()
        ax3D = fig.add_subplot(111, projection='3d')
        ax3D.set_zlim(95,120)
        label = ax3D.set_xlabel('Window Size')
        label = ax3D.set_ylabel('Centroid Numbers')
        label = ax3D.set_zlabel('Price')
        ax3D.set_title("%03d"%i)
        #ax3D.set_axis_off()
        plot=get_3D_plot(ax3D ,ratio=i,color="#ff0000")
        with open("plot%03d.png"%i,"w") as f:
            #print("%ld"%((1.0*key/len(domain))*360))
            plt.savefig(f, format='png')
            plt.close()
        #print("%03d"%i)


    #plt.show(block=False)
    #raw_input("...")
