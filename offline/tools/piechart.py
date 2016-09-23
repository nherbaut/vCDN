#!/usr/bin/env python
import argparse
import collections
import csv
import os

import matplotlib.pyplot as plt
import numpy as np

CUTOFF = 2 / 100.0
import matplotlib as mpl

mpl.rcParams['font.size'] = 16


def do_plot(file):
    title = os.path.basename(file)[:-5]
    fig = plt.figure()
    ax = fig.gca()

    # read the file
    data = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    data_pc = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    print("%s" % file)
    with open(file) as f:

        for name, bw, type in filter(lambda x: len(x) == 3, list(csv.reader(f))):
            data[type][name] += float(bw) / 1000.0

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

    colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']

    sizes_cat = [np.sum([data[a][b] for b in sorted(data[a])]) for a in sorted(data) if a != "Content"]
    sizes_cat_labels = ["%s (%1.1lf Gbps)" % (a, np.sum(data[a].values())) for a in sorted(data) if a != "Content"]
    sizes_content = [data[a][b] for a in sorted(data) for b in sorted(data[a]) if a == "Content" if
                     data_pc[a][b] > CUTOFF]
    sizes_content_other_content = np.sum([data[a][b] for a in sorted(data) for b in sorted(data[a]) if a == "Content" if
                                          data_pc[a][b] <= CUTOFF])
    sizes_content_labels = ["%s (%1.1lf Gbps)" % (b, data[a][b]) for a in sorted(data) for b in sorted(data[a]) if
                            a == "Content" if data_pc[a][b] > CUTOFF]

    sizes_content.append(sizes_content_other_content)
    sizes_content_labels.append("Other Content (%1.1lf Gbps)" % sizes_content[-1])

    from colour import Color
    grey = Color("#cccccc")
    red = Color("red")
    orange = Color("#880000")

    color_cat = [c.get_hex_l() for c in grey.range_to(Color("white"), len(sizes_cat))]
    color_content = [c.get_hex_l() for c in red.range_to(orange, len(sizes_content))]

    wedges, texts, _ = ax.pie(np.append(sizes_cat, sizes_content),
                              labels=np.append(sizes_cat_labels, sizes_content_labels),
                              colors=np.append(color_cat, color_content), radius=1.5, autopct='%1.1f%%', startangle=90,
                              shadow=True, )

    for wedge in wedges[len(color_cat):]:
        wedge.set_lw(2)

    plt.xkcd()
    ax.autoscale(True)
    ax.set_title(title)
    plt.savefig("pie.svg")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='draw a pie chart for AS compositions')
    parser.add_argument('--file', '-f', type=str, default="/home/nherbaut/tmp/data.csv")
    args = parser.parse_args()
    file = args.file
    do_plot(file)
