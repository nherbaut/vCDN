#!/usr/bin/env python
import argparse
import collections

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import spline

parser = argparse.ArgumentParser(description='launch time simu')
parser.add_argument('--file', '-f', type=str, default="/home/nherbaut/tmp/data.csv")

args = parser.parse_args()
file = args.file

pdata = collections.defaultdict(lambda: [])

with open(file) as f:
    for data in f.read().split("\n"):
        if len(data.split("\t")) == 3:
            curve, x, y, = data.split("\t")
            pdata[curve].append((float(x), float(y)))

fig, ax1 = plt.subplots()
for key in sorted(pdata.keys()):
    if len(pdata[key]) :
        xs, ys = zip(*sorted(pdata[key], key=lambda x: x[0]))
        x_sm = np.array(xs)
        y_sm = np.array(ys)


        x_smooth = np.linspace(x_sm.min(), x_sm.max(), 10)
        y_smooth = spline(x_sm, y_sm, x_smooth,order=2)

        #ax1.plot(x_smooth, y_smooth, label=key)
        ax1.plot(xs, ys, label=key)
        ax1.legend()
plt.show(block=True)

xs=[]
ys=[]
for key in sorted(pdata.keys()):
    xs.append(float(key))
    index_min=np.argmin(list(zip(*pdata[key]))[1])
    ys.append(list(zip(*pdata[key]))[0][index_min])

fig, ax1 = plt.subplots()
ax1.plot(xs,ys,label="best discount price per migration cost")
ax1.set_xscale('log')
ax1.set_ylim(np.min(ys)*0.9,np.max(ys)*1.1)

z = np.polyfit(np.log(xs), ys, 1)
p = np.poly1d(z)
ax1.plot(xs,p(np.log(xs)),"r--",label="y=%.6f log(x)+ %.6f "%(z[0],z[1]))
ax1.legend()
plt.show(block=True)
plt.close()
plt.cla()
plt.clf()



