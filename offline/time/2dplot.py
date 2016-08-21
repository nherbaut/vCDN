#!/usr/bin/env python
#from a file, plot
import argparse

import locale
from SLA3D import *

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='1 iteration for solver')
    parser.add_argument('--file',"-f", default="forecast.csv",type=str)
    parser.add_argument('--windows',"-w", default=5,type=int)
    parser.add_argument('--centroids',"-c", default=5,type=int)
    parser.add_argument('--plot', dest="plot", action="store_true")
    args = parser.parse_args()


    df = pd.read_csv(args.file)
    plt.figure();
    df.plot();
    plt.show()
    # convert time column to proper time
    ts = pd.Series(data=df["fcmean"].values,index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),axis=1).values)
    #tsr=ts.resample("1H").max().ffill()
    tsr = ts

    # original_integration=np.trapz(ts.values, ts.index.astype(np.i nt64))
    # overhead=(np.trapz(tse.values, tse.index.astype(np.int64))-original_integration)/original_integrati on*100
    # print("%d %d %lf" % (win,ncentroids,overhea d ))

    tse = get_tse(tsr, args.windows, args.centroids )

    if args.plot:
        ax = plt.axes(xlim=[tsr.index[0], tsr.index[-1]], ylim=[min(tsr) * 0.75, max(tsr) * 1.25])
        ax.xaxis_date()
        ax.plot(tsr.index, tse, zorder=1)
        ax.fill_between(tsr.index, tsr, tse, where=tse >= tsr, facecolor='red', interpolate=True)
        ax.fill_between(tsr.index, tsr, 0, where=tsr >= 0, facecolor='green', interpolate=True)
        #locale.format("price is %ld"%price_slas(chunk_serie_as_sla(tse)),  grouping=True)
        plt.title("price is %s" %locale.format("%d",price_slas(chunk_serie_as_sla(tse)),  grouping=True))
        plt.show(block=True)
    else:
        print("price is %s" %locale.format("%d",price_slas(chunk_serie_as_sla(tse)),  grouping=True))



