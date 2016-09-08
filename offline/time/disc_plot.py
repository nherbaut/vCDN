#!/usr/bin/env python
# from a file, plot
import locale

import matplotlib.pyplot as plt
import pandas as pd

from ..time.SLA3D import get_tse

locale.setlocale(locale.LC_ALL, 'en_US.utf8')


def plot_forecast_and_disc_and_total(tsr, windows, centroids, plot_name="default", out_file_name="default.svg",total_sla_plot=None):
    plt.close('all')
    plot_count = len(tsr)
    tse_sum = pd.Series()
    for index, (plot_name, data) in enumerate(tsr.items(), start=1):
        tse1 = get_tse(data[0], windows, centroids)
        tse_sum=pd.Series.add(tse_sum, tse1, fill_value=0)
        ax = plt.subplot((plot_count+1) / 2+1, 2, index)
        ax.set_xlim([data[0].index[0], data[0].index[-1]])
        ax.set_ylim([min(data[0]) * 0.75, max(data[0]) * 1.25])
        ax.xaxis_date()

        ax.plot(data[0].index, tse1, zorder=3)

        ax.fill_between(data[0].index, tse1, 0, where=tse1 >= data[0], facecolor='red', interpolate=True, alpha=0.2,
                        zorder=2,
                        label="discretization (%d,%d)" % (windows, centroids), linewidth=3)
        ax.fill_between(data[0].index, data[0], 0, where=data[0] >= 0, facecolor='green', interpolate=True, alpha=1,
                        zorder=3,
                        hatch="/", label="traffic prediction", linewidth=0)
        ax.set_title(plot_name)

    ax = plt.subplot((plot_count+1) / 2+1, 2, index + 1)
    ax.set_xlim(tse_sum.index[0], tse_sum.index[-1])
    ax.set_ylim([min(tse_sum) * 0.75, max(tse_sum) * 1.25])
    ax.xaxis_date()
    ax.fill_between(tse_sum.index, tse_sum, 0, where=tse_sum >= 0, facecolor='red', interpolate=True, alpha=0.2,
    zorder = 2,
    label = "discretization (%d,%d)" % (windows, centroids), linewidth = 3)
    ax.set_title("Discretization sum")

    ax = plt.subplot((plot_count + 1) / 2+1, 2, index + 2)
    ax.set_xlim(total_sla_plot.index[0], total_sla_plot.index[-1])
    ax.set_ylim([min(total_sla_plot) * 0.75, max(total_sla_plot) * 1.25])
    ax.xaxis_date()
    ax.fill_between(total_sla_plot.index, total_sla_plot, 0, where=total_sla_plot>= 0, facecolor='red', interpolate=True, alpha=0.2,
                    zorder=2,
                    label="discretization (%d,%d)" % (windows, centroids), linewidth=3)
    ax.set_title("Discretization sum reconstituted")




    plt.savefig(out_file_name)
    plt.show(block=False)
