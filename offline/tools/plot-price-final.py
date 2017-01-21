#!/usr/bin/env python
import argparse
import collections

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import spline
import matplotlib.ticker as mtick
parser = argparse.ArgumentParser(description='launch time simu')
parser.add_argument('--file', '-f', type=str, default="/home/nherbaut/tmp/data.csv")

args = parser.parse_args()
file = args.file

pdata = collections.defaultdict(lambda: [])

with open(file) as f:
    for data in f.read().split("\n"):
        if len(data.split("\t")) == 4:
            mig_price, discount, isp_price, cdn_price= data.split("\t")
            pdata[mig_price].append((float(discount), float(isp_price), float(cdn_price)))


for key in sorted(pdata.keys()):
    if len(pdata[key]) > 3:
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        discounts, isp_prices, cdn_price= list(zip(*sorted(pdata[key], key=lambda x: x[0])))
        discounts=np.array(discounts)*100

        fmt = '%.0f%%'  # Format you want the ticks, e.g. '40%'
        xticks = mtick.FormatStrFormatter(fmt)
        ax1.xaxis.set_major_formatter(xticks)

        ax1.grid()

        #x_smooth = np.linspace(x_sm.min(), x_sm.max(), 10)
        #y_smooth = spline(x_sm, y_sm, x_smooth,order=2)

        #ax1.plot(x_smooth, y_smooth, label=key)
        ax1.plot(discounts, isp_prices, label="System + Network Cost for ISP")
        ax2.plot(discounts, cdn_price, label="SLA embedding price for CDN",color="r")

        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()

        plt.legend(h1 + h2, l1 + l2, loc='best', )
        plt.savefig("discount-price-isp-cdn-comparizon-%s.svg"%key)
        plt.show(block=True)
        #break





discounts=[]
isp_prices=[]
for key in sorted(pdata.keys()):
    discounts.append(float(key))
    #index_min=np.argmin(list(zip(*pdata[key]))[1])
    #take the first on that is 10% higher than the min
    t = list(zip(*pdata[key]))[1]
    min_generator = (i for i, v in enumerate(t) if v < (np.min(t) * 1.3))
    isp_prices.append(list(zip(*pdata[key]))[0][next(min_generator)])

fig, ax1 = plt.subplots()
ax1.plot(discounts, isp_prices, label="best discount price per migration cost")
ax1.set_xscale('log')
ax1.set_ylim(np.min(isp_prices) * 0.9, np.max(isp_prices) * 1.1)

z = np.polyfit(np.log(discounts), isp_prices, 1)
p = np.poly1d(z)
ax1.plot(discounts, p(np.log(discounts)), "r--", label="y=%.6f log(x)+ %.6f " % (z[0], z[1]))
ax1.legend()
plt.show(block=True)
plt.close()
plt.cla()
plt.clf()



