#!/usr/bin/env python
import re

import matplotlib.pyplot as plt


def plot_all_results(init_bw, init_cpu, res, init_point,id):
    plt.figure(0)
    plot_results_bw(res, init_point, init_bw, init_cpu,id)
    plt.figure(1)
    plot_results_cpu(res, init_point, init_bw, init_cpu,id)
    plt.figure(2)
    plot_results_transfo(res, init_point, init_bw, init_cpu,id)


def plot_results_transfo(res, init_point, init_bw, init_cpu, id):
    vhg = plt.plot([float(x.split("\t")[2]) for x in res["vhg"]][init_point:],
                   [float(x.split("\t")[3]) for x in res["vhg"]][init_point:],
                   'b', label="vhg",
                   linestyle="solid")

    vcdn = plt.plot([float(x.split("\t")[2]) for x in res["vcdn"]][init_point:],
                    [float(x.split("\t")[3]) for x in res["vcdn"]][init_point:],
                    'y', label="vcdn",
                    linestyle="solid")
    all = plt.plot([float(x.split("\t")[2]) for x in res["all"]][init_point:],
                   [float(x.split("\t")[3]) for x in res["all"]][init_point:],
                   'g', label="all",
                   linestyle="solid")

    plt.ylabel("# for transformation required by embedding")
    plt.xlabel('# of Embeded SLA')
    plt.legend(["vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    plt.savefig("transfo%d.pdf" % id, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)
    plt.clf()


def plot_results_cpu(res, init_point, init_bw, init_cpu, id):
    none = plt.plot([float(x.split("\t")[2]) for x in res["none"]][init_point:],
                    [100 - float(x.split("\t")[1]) / init_cpu * 100 for x in res["none"]][init_point:],
                    'r', label="none",
                    linestyle="solid")

    vhg = plt.plot([float(x.split("\t")[2]) for x in res["vhg"]][init_point:],
                   [100 - float(x.split("\t")[1]) / init_cpu * 100 for x in res["vhg"]][init_point:],
                   'b', label="vhg",
                   linestyle="solid")

    vcdn = plt.plot([float(x.split("\t")[2]) for x in res["vcdn"]][init_point:],
                    [100 - float(x.split("\t")[1]) / init_cpu * 100 for x in res["vcdn"]][init_point:],
                    'y', label="vcdn",
                    linestyle="solid")
    all = plt.plot([float(x.split("\t")[2]) for x in res["all"]][init_point:],
                   [100 - float(x.split("\t")[1]) / init_cpu * 100 for x in res["all"]][init_point:],
                   'g', label="all",
                   linestyle="solid")

    plt.legend(["Canonical", "vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    plt.ylabel('% of Substrate Node Capacity Usage')
    plt.xlabel('# of Embeded SLA')
    # plt.show()


    plt.savefig("node-capacities%d.pdf" % id, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)
    plt.clf()


def plot_results_bw(res, init_point, init_bw, init_cpu, id):
    none = plt.plot([float(x.split("\t")[2]) for x in res["none"]][init_point:],
                    [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["none"]][init_point:],
                    'r', label="none",
                    linestyle="solid")

    vhg = plt.plot([float(x.split("\t")[2]) for x in res["vhg"]][init_point:],
                   [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["vhg"]][init_point:],
                   'b', label="vhg",
                   linestyle="solid")
    vcdn = plt.plot([float(x.split("\t")[2]) for x in res["vcdn"]][init_point:],
                    [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["vcdn"]][init_point:],
                    'y', label="vcdn",
                    linestyle="solid")
    all = plt.plot([float(x.split("\t")[2]) for x in res["all"]][init_point:],
                   [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["all"]][init_point:],
                   'g', label="all",
                   linestyle="solid")

    plt.legend(["Canonical", "vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    plt.ylabel('% of Substrate Bandwidth Usage')
    plt.xlabel('# of Embeded SLA')
    # plt.show()
    plt.savefig("edge-capacities%d.pdf" % id, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)

    plt.clf()


def plotsol():
    edges = []
    nodesdict = {}
    with open("substrate.edges.data", 'r') as f:
        data = f.read()
        for line in data.split("\n"):
            line = line.split("\t")
            if len(line) == 4:
                edges.append(line)

    with open("substrate.nodes.data", 'r') as f:
        data = f.read()
        for line in data.split("\n"):

            line = line.split("\t")
            if (len(line) == 2):
                nodesdict[line[0]] = line[1]

    with open("solutions.data", "r") as sol:
        data = sol.read().split("\n")
        nodesSol = []
        edgesSol = []
        for line in data:
            matches = re.findall("x\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                nodesSol.append(matches[0])
                continue
            matches = re.findall("y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                edgesSol.append(matches[0])
                continue

    with open("substrate.dot", 'w') as f:
        f.write("digraph{rankdir=LR;\n\n\n\n subgraph{\n\n\n")

        avgcpu = reduce(lambda x, y: float(x) + float(y), nodesdict.values(), 0.0) / len(nodesdict)

        for node in nodesdict.items():
            # f.write("%s [label=%2.2f,shape=box,color=black,width=%f];\n"%(node[0],float(node[1]),min	(1,float(node[1])/avgcpu)))
            f.write("%s [shape=box,color=black,width=%f,fontsize=20];\n" % (node[0], min(1, float(node[1]) / avgcpu)))

        avgbw = [float(edge[2]) for edge in edges]
        avgbw = sum(avgbw) / len(avgbw)

        avgdelay = reduce(lambda x, y: float(x) + float(y[3]), edges, 0.0) / len(edge)
        for edge in edges:
            availbw = float(edge[2])
            # f.write("%s->%s [ label=\"%d\", penwidth=\"%d\", fontsize=20];\n " % (edge[0], edge[1], float(edge[2]), 1+3*availbw/avgbw))
            f.write("%s->%s [  penwidth=\"%d\", fontsize=20];\n " % (edge[0], edge[1], 3))

        for node in nodesSol:
            f.write("%s->%s[color=red];\n" % node)
            f.write("%s[shape=circle,fillcolor=azure3,style=filled,fontsize=24];\n" % node[1])

        f.write("}")

        f.write("\nsubgraph{\n edge[color=blue3,weight=0];\n")
        for edge in edgesSol:
            f.write("%s->%s [ style=dashed,label=\"%s-->%s\",fontcolor=blue3 ,fontsize=20,penwidth=3];\n " % (edge))

        f.write("}\n\n")
        f.write("}")
