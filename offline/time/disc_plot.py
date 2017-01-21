#!/usr/bin/env python
# from a file, plot
import locale

import matplotlib.pyplot as plt
import pandas as pd

from ..time.SLA3D import get_tse

locale.setlocale(locale.LC_ALL, 'C')


def plot_forecast_and_disc_and_total(tsr, windows, centroids, plot_name="default", out_file_name="default.svg",total_sla_plot=None):
    plt.close('all')
    plot_count = len(tsr)
    tse_sum = pd.Series()
    for index, (plot_name, data) in enumerate(list(tsr.items()), start=1):
        time_serie=data[1]
        tse1 = get_tse(time_serie, windows, centroids)
        tse_sum=pd.Series.add(tse_sum, tse1, fill_value=0)
        ax = plt.subplot((plot_count+1) / 2+1, 2, index)
        ax.set_xlim([time_serie.index[0], time_serie.index[-1]])
        ax.set_ylim([min(time_serie) * 0.75, max(time_serie) * 1.25])
        ax.xaxis_date()

        ax.plot(time_serie.index, tse1, zorder=3)

        ax.fill_between(time_serie.index, tse1, 0, where=tse1 >= time_serie, facecolor='red', interpolate=True, alpha=0.2,
                        zorder=2,
                        label="discretization (%d,%d)" % (windows, centroids), linewidth=3)
        ax.fill_between(time_serie.index, time_serie, 0, where=time_serie >= 0, facecolor='green', interpolate=True, alpha=1,
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
