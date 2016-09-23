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

    args = parser.parse_args()

    df = pd.read_csv(args.file)


    # convert time column to proper time
    tsr = pd.Series(data=df["fc0"].values,
                    index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                   axis=1).values)

    tsrmean = pd.Series(data=df["fcmean"].values,
                      index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                     axis=1).values)


    tsr95 = pd.Series(data=df["fc95"].values,
                    index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                   axis=1).values)

    tsr80 = pd.Series(data=df["fc80"].values,
                      index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                     axis=1).values)

    tsr50 = pd.Series(data=df["fc50"].values,
                      index=df.apply(lambda row: datetime.datetime.strptime(row['Index'], '%Y-%m-%d %H:%M:%S'),
                                     axis=1).values)





    ax = plt.axes(xlim=[tsr.index[0], tsr.index[-1]], ylim=[min(tsr) * 0.75, max(tsr) * 1.25], zorder=2)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)



    ax.plot(tsr95,label="95% CI ",linewidth=2,color="#8888ff",alpha=0.2)
    ax.plot(tsr80,label="80% CI ",linewidth=2,color="#4444ff",alpha=0.2)
    ax.plot(tsr50,label="50% CI ",linewidth=2,color="#0000ff",alpha=0.2)
    ax.plot(tsr, label="observations", linewidth=5,color="red",zorder=3)

    ax.plot(np.maximum(0,2*tsrmean-tsr95),linewidth=2,color="#8888ff",alpha=0.2)
    ax.plot(np.maximum(0,2*tsrmean-tsr80),linewidth=2,color="#4444ff",alpha=0.2)
    ax.plot(np.maximum(0,2*tsrmean-tsr50),linewidth=2,color="#0000ff",alpha=0.2)


    ax.fill_between(tsr.index, tsr50, tsr,  facecolor='#0000ff', alpha=0.2, zorder=2,)
    ax.fill_between(tsr.index, tsr80, tsr, facecolor='#4444ff', alpha=0.2, zorder=2, )
    ax.fill_between(tsr.index, tsr95, tsr, facecolor='#8888ff', alpha=0.2, zorder=2, )

    ax.fill_between(tsr.index, np.maximum(0,2*tsrmean-tsr50), tsr, facecolor='#0000ff', alpha=0.2, zorder=2, )
    ax.fill_between(tsr.index, np.maximum(0,2*tsrmean-tsr80), tsr, facecolor='#4444ff', alpha=0.2, zorder=2, )
    ax.fill_between(tsr.index, np.maximum(0,2*tsrmean-tsr95), tsr, facecolor='#8888ff', alpha=0.2, zorder=2, )

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
              fancybox=True, shadow=True, ncol=5)
    plt.savefig("forecast_plot.svg", bbox_inches='tight')
    plt.show(block=True, )


    ax = plt.axes(xlim=[tsr.index[0], tsr.index[-1]], ylim=[min(tsr) * 0.75, max(tsr) * 1.25], zorder=2)




    tse1 = get_tse(tsr, args.windows1, args.centroids1)
    tse2 = get_tse(tsr, args.windows2, args.centroids2)

    ax.plot(tsr.index, tse1, zorder=3,linewidth=3,alpha=0.5)
    ax.plot(tsr.index, tse2, zorder=4,linewidth=3,alpha=0.5)

    ax.fill_between(tsr.index, tse1, 0, where=tse1 >= tsr, facecolor='#ff8888',  alpha=0.5, zorder=2,
                    label="discretization (%d,%d)" % (args.windows1, args.centroids1))
    ax.fill_between(tsr.index, tse2, 0, where=tse2 >= tsr, facecolor='#0000ff',  alpha=0.8, zorder=2,
                    label="discretization (%d,%d)" % (args.windows2, args.centroids2))
    ax.fill_between(tsr.index, tsr, 0, where=tsr >= 0, facecolor='green', interpolate=True, alpha=1, zorder=3,
                     label="traffic prediction", linewidth=3)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
              fancybox=True, shadow=True, ncol=5)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    # locale.format("price is %ld"%price_slas(chunk_serie_as_sla(tse)),  grouping=True)
    # plt.title("price is %s" %locale.format("%d",price_slas(chunk_serie_as_sla(tse)),  grouping=True))
    plt.savefig("discretize_plot.svg",bbox_inches='tight')
    plt.show(block=True,)

