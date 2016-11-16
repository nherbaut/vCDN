#!/usr/bin/env python
import hashlib
import os
import subprocess

import matplotlib.pyplot as plt
import numpy

OPTIM_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../optim')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

x_resolution = 5


def plot_all_results(res, min_plot, max_plot, id=999):
    plt.figure(0)
    plot_results_bw(res, min_plot, max_plot, id)
    plt.figure(1)
    plot_results_cpu(res, min_plot, max_plot, id)
    plt.figure(2)
    plot_results_embedding(res, min_plot, max_plot, id)


def plot_results_cpu(res, min_plot, max_plot, id):
    legend = []
    for key in sorted(res.keys()):
        spec = get_display_style(key, res)
        init_value = res[key][0].substrate.get_nodes_sum()
        plt.plot([x[0] for x in enumerate(res[key][min_plot:max_plot])],
                 [100 - x.substrate.get_nodes_sum() / init_value * 100 for x in res[key][min_plot:max_plot]],
                 color=spec["color"],
                 label=spec["label"],
                 linestyle=spec["linestyle"], marker=spec["marker"], markevery=10, linewidth=2,
                 )
        legend.append(spec["label"])

    ax = plt.subplot(111)
    plt.grid()
    ax.set_xticks(
        numpy.arange(0, len(res[key][min_plot:max_plot]), max(1, len(res[key][min_plot:max_plot]) / x_resolution)))
    ax.set_yticks(numpy.arange(0, 140, 20))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
              ncol=3, fancybox=True, shadow=True)
    plt.ylabel('% of Substrate Node Capacity Usage')
    plt.xlabel('# of Embeded requests')
    # plt.show()


    plt.savefig("%d-node-capacitie.pdf" % id, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)
    subprocess.Popen(["evince", os.path.join(RESULTS_FOLDER, "%d-node-capacitie.pdf" % id)])
    plt.clf()


def plot_results_embedding(res, min_plot, max_plot, id):
    legend = []
    for key in sorted(res.keys()):
        spec = get_display_style(key, res)
        init_value = res[key][0].substrate.get_nodes_sum()
        plt.plot([x[0] for x in enumerate(res[key][min_plot:max_plot])],
                 [x.success_rate * 100 for x in res[key][min_plot:max_plot]],
                 color=spec["color"],
                 label=spec["label"],
                 linestyle=spec["linestyle"], marker=spec["marker"], markevery=10, linewidth=2,
                 )
        legend.append(spec["label"])

    ax = plt.subplot(111)
    plt.grid()
    ax.set_xticks(
        numpy.arange(0, len(res[key][min_plot:max_plot]), max(1, len(res[key][min_plot:max_plot]) / x_resolution)))
    ax.set_yticks(numpy.arange(0, 140, 20))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
              ncol=3, fancybox=True, shadow=True)
    plt.ylabel('% of successful embedding')
    plt.xlabel('# of Embeded requests')
    # plt.show()


    plt.savefig("%d-embedding.pdf" % id, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)
    subprocess.Popen(["evince", os.path.join(RESULTS_FOLDER, "%d-embedding.pdf" % id)])
    plt.clf()


def get_display_style(name, res):
    ls = res[name][0].linestyle
    color = "#" + hashlib.sha1("0sdsqd" + name).hexdigest()[0:6]
    results = {}

    if name == "none":
        results = {'color': color, 'label': "Canonical", 'linestyle': ls}
    elif name == "vhg":
        results = {'color': color, 'label': "VHG", 'linestyle': ls}
    elif name == "vcdn":
        results = {'color': color, 'label': "VCDN", 'linestyle': ls}
    elif name == "all":
        results = {'color': color, 'label': "VHG+VCDN", 'linestyle': ls}
    else:
        results = {'color': color, 'label': name, 'linestyle': ls}
    results["marker"] = res[name][0].marker

    return results


def plot_results_bw(res, min_plot, max_plot, id):
    legend = []
    for key in sorted(res.keys()):
        spec = get_display_style(key, res)
        init_value = res[key][0].substrate.get_edges_sum()

        plt.plot([x[0] for x in enumerate(res[key][min_plot:max_plot])],
                 [100 - x.substrate.get_edges_sum() / init_value * 100 for x in res[key][min_plot:max_plot]],
                 color=spec["color"],
                 label=spec["label"],
                 linestyle=spec["linestyle"], marker=spec["marker"], markevery=10, linewidth=2,

                 )

        legend.append(spec["label"])

    ax = plt.subplot(111)
    plt.grid()
    ax.set_xticks(
        numpy.arange(0, len(res[key][min_plot:max_plot]), max(1, len(res[key][min_plot:max_plot]) / x_resolution)))
    ax.set_yticks(numpy.arange(0, 140, 20))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
              ncol=3, fancybox=True, shadow=True)
    plt.ylabel('% of Substrate Bandwidth Usage')
    plt.xlabel('# of Embeded Requests')
    # plt.show()
    plt.savefig(os.path.join(RESULTS_FOLDER, "%d-edge-capacities.pdf" % id), dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)

    subprocess.Popen(["evince", os.path.join(OPTIM_FOLDER, "%d-edge-capacities.pdf" % id)])
    plt.clf()


def plotsol_from_db(**kwargs):
    edges = []
    nodesdict = {}
    cdn_candidates = []
    starters_candiates = []
    nodesSol = []
    edgesSol = []
    net = kwargs["net"]
    service = kwargs.get("service", None)
    dest_folder = kwargs.get("dest_folder", RESULTS_FOLDER)
    if service is not None:
        su = service.slas[0].substrate
    else:
        su = kwargs["substrate"]

    if not net:  # we don't display solution, only substrate
        mapping = service.mapping
        if mapping is None:
            raise ValueError("no mapping for service")

        cdn_candidates = mapping.dump_cdn_node_mapping()
        starters_candiates = mapping.dump_starter_node_mapping()
        nodesSol = mapping.dump_node_mapping()
        edgesSol = mapping.dump_edge_mapping()

    edges = [(edge.node_1.name, edge.node_2.name, edge.bandwidth, edge.delay) for edge in su.edges]

    nodesdict = {node.name: node.cpu_capacity for node in su.nodes}

    with open(os.path.join(dest_folder, "substrate.dot"), 'w') as f:
        f.write("graph{rankdir=LR;overlap = voronoi;\n\n\n\n subgraph{\n\n\n")
        # f.write("graph{rankdir=LR;\n\n\n\n subgraph{\n\n\n")



        for node in nodesdict.items():
            if node[0] in starters_candiates:
                color = "green1"
            elif node[0] in cdn_candidates:
                color = "red1"
            else:
                color = "black"
            f.write("\"%s\" [shape=box,style=filled,fillcolor=white,color=%s,width=%f,fontsize=15];\n" % (
                node[0], color, 1,))

        for edge in edges:
            f.write("\"%s\"--\"%s\" [penwidth=\"%d\",fontsize=15,len=2,label=\" \" id=\"%s--%s\"];\n " % (edge[0], edge[1], 3,edge[0], edge[1]))

        for node in nodesSol:
            if "S0" not in node[1]:
                f.write("\"%s\"--\"%s\" [color=blue,len=1.5,label=\" \"  ];\n" % node)
                name = node[1]

                if "VHG" in node[1]:
                    color = "azure1"
                    shape = "circle"

                elif "vCDN".lower() in node[1].lower():
                    color = "azure3"
                    shape = "circle"
                elif "S" in node[1]:
                    color = "green"
                    shape = "doublecircle"
                else:
                    color = "red"
                    shape = "doublecircle"

                f.write("\"%s\" [shape=%s,fillcolor=%s,style=filled,fontsize=12];\n" % (name, shape, color))
        f.write("}")

        f.write("\nsubgraph{\n edge[color=chartreuse,weight=0];\n")
        for edge in edgesSol:
            if "S0" not in edge[2]:
                f.write("\"%s\"--\"%s\" [ style=dashed,label=\"%s&#8594;%s\",fontcolor=blue3 ,fontsize=12,penwidth=%d];\n " % (
                    edge + (kwargs["service_link_linewidth"],)))

        f.write("}\n\n")
        f.write("}")
