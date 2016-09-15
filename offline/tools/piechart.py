#!/usr/bin/env python
import argparse
import collections
import csv

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection


def do_plot(file):
    fig = plt.figure()
    ax = fig.gca()

    # read the file
    data = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    data_pc = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    print("%s" % file)
    with open(file) as f:

        for name, bw, type in filter(lambda x: len(x) == 3, list(csv.reader(f))):
            data[type][name] += float(bw)

    # get the %
    total_size = np.sum([data[a][b] for a in data for b in data[a]])
    for key1 in data:
        for key2 in data[key1]:
            data_pc[key1][key2] = data[key1][key2] * 1.0 / total_size

    for type in data.keys():
        print("%s" % type)
        for name in data[type]:
            print("\t%s:%lf%% or %lf" % (name, 100 * data_pc[type][name], data[type][name]))

    # solution here: http://stackoverflow.com/questions/20549016/explode-multiple-slices-of-pie-together-in-matplotlib


    ax.set_aspect('equal')
    ax.axis('off')
    sizes_cat = [np.sum([data[a][b] for b in sorted(data[a])]) for a in sorted(data) if a != "Content"]
    sizes_cat_labels = ["%s (%1.1lf%%)" % (a, np.sum(100*data_pc[a].values())) for a in sorted(data) if a != "Content"]
    sizes_content = [data[a][b] for a in sorted(data) for b in sorted(data[a]) if a == "Content"]
    sizes_content_labels = ["%s (%1.1lf%%)" % (b, 100*data_pc[a][b]) for a in sorted(data) for b in sorted(data[a]) if a == "Content"]
    # explodes = np.append(np.zeros(len(sizes_cat_labels)), np.ones(len(sizes_content_labels)))

    wedges, texts = ax.pie(np.append(sizes_cat, sizes_content),
                           labels=np.append(sizes_cat_labels, sizes_content_labels),
                           startangle=90, )

    groups = [range(3, 14)]
    radfraction = 0.3
    patches = []
    for i in groups:
        ang = np.deg2rad((wedges[i[-1]].theta2 + wedges[i[0]].theta1) / 2, )
        for j in i:
            we = wedges[j]
            center = (radfraction * we.r * np.cos(ang), radfraction * we.r * np.sin(ang))
            patches.append(mpatches.Wedge(center, we.r, we.theta1, we.theta2))

    colors = np.linspace(0, 1, len(patches))
    collection = PatchCollection(patches, cmap=plt.cm.hsv)
    collection.set_array(np.array(colors))
    # ax.add_collection(collection)
    ax.autoscale(True)
    plt.savefig("pie.svg")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='launch time simu')
    parser.add_argument('--file', '-f', type=str, default="/home/nherbaut/tmp/data.csv")
    args = parser.parse_args()
    file = args.file
    do_plot(file)
