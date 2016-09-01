from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import os

from ..time.slagen import *
DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')

def plot_3D_slas(forecasts):

    fig = plt.figure()

    ax = fig.add_subplot(111, projection='3d')
    #for c, z in zip(['r', 'g', 'b', 'y'], [30, 20, 10, 0]):
    colors=["r","g","b","y"]
    for key,value in [(key*5,value) for (key,value) in enumerate(forecasts,start=1)]:
        xs = value.index
        ys = [value[x] for x in xs]

        # You can provide either a single color or an array. To demonstrate this,
        # the first bar of each set will be colored cyan.
        cs = [colors[(key/5)%len(colors)]] * len(xs)
        cs[0] = 'c'
        ax.bar(xs, ys, zs=key, zdir='y', color=cs, alpha=0.5,width=0.05)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    plt.show()



data_files = []
for file in sorted(os.listdir(DATA_FOLDER)):
    if file.endswith("-daily_1H.csvx"):
        data_files.append(file)


tses = {file: get_forecast(os.path.join(DATA_FOLDER, file), 1, 20) for file in data_files[3:7]}

plot_3D_slas(tses.values())