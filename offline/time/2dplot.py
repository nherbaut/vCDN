#!/usr/bin/env python
# from a file, plot
import argparse
import datetime
import locale

from SLA3D import *

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='1 iteration for solver')
    parser.add_argument('--file', "-f", default="forecast.csv", type=str)
    parser.add_argument('--windows1', default=5, type=int)
    parser.add_argument('--centroids1', default=5, type=int)
    parser.add_argument('--windows2', default=3, type=int)
    parser.add_argument('--centroids2', default=10, type=int)
    parser.add_argument('--plot', dest="plot", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(args.file)
    # plt.figure();
    df.plot();
    plt.show()
    # convert time column to proper time
    tsr = pd.Series(data=df["fcmean"].values,
                    index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                   axis=1).values)


    tse1 = get_tse(tsr, args.windows1, args.centroids1)
    tse2 = get_tse(tsr, args.windows2, args.centroids2)

    if args.plot:
        ax = plt.axes(xlim=[tsr.index[0], tsr.index[-1]], ylim=[min(tsr) * 0.75, max(tsr) * 1.25], zorder=2)
        ax.xaxis_date()

        ax.plot(tsr.index, tse1, zorder=3)
        ax.plot(tsr.index, tse2, zorder=4)

        ax.fill_between(tsr.index, tse1, 0, where=tse1 >= tsr, facecolor='red', interpolate=True, alpha=0.2, zorder=2,
                        label="discretization (%d,%d)" % (args.windows1, args.centroids1), linewidth=3)
        ax.fill_between(tsr.index, tse2, 0, where=tse2 >= tsr, facecolor='blue', interpolate=True, alpha=0.2, zorder=2,
                        label="discretization (%d,%d)" % (args.windows2, args.centroids2), linewidth=3)
        ax.fill_between(tsr.index, tsr, 0, where=tsr >= 0, facecolor='green', interpolate=True, alpha=1, zorder=3,
                        hatch="/", label="traffic prediction", linewidth=0)
        ax.legend()

        # locale.format("price is %ld"%price_slas(chunk_serie_as_sla(tse)),  grouping=True)
        # plt.title("price is %s" %locale.format("%d",price_slas(chunk_serie_as_sla(tse)),  grouping=True))
        plt.savefig("test.svg")
        plt.show(block=True)

    else:
        print("price is %s" % locale.format("%d", price_slas(chunk_serie_as_sla(tse)), grouping=True))
