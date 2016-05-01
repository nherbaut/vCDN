#!/usr/bin/env python
import re
import subprocess
import matplotlib.pyplot as plt
import tempfile

def plot_all_results( res, init_point=0,id=999):
    plt.figure(0)
    plot_results_bw(res, init_point, id)
    plt.figure(1)
    plot_results_cpu(res, init_point,id)
    plt.figure(2)
    plot_results_embedding(res, init_point, id)



def plot_results_cpu(res, init_point, id):
    for key in res.keys():
        spec=get_display_style(key)
        init_value=res[key][0].substrate.get_nodes_sum()
        plt.plot([x[0] for x in enumerate(res[key][init_point:])],
                 [100 - x.substrate.get_nodes_sum()/init_value*100 for x in res[key][init_point:]],
                 color=spec["color"],
                 label=spec["label"],
                 linestyle=spec["linestyle"],
                 )

    plt.legend(["Canonical", "vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    plt.ylabel('% of Substrate Node Capacity Usage')
    plt.xlabel('# of Embeded requests')
    # plt.show()


    plt.savefig("%d-node-capacitie.pdf" % id, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)
    plt.clf()

def plot_results_embedding(res, init_point,  id):

    for key in res.keys():
        spec=get_display_style(key)
        init_value=res[key][0].substrate.get_nodes_sum()
        plt.plot([x[0] for x in enumerate(res[key][init_point:])],
                 [x.success_rate for x in res[key][init_point:]],
                 color=spec["color"],
                 label=spec["label"],
                 linestyle=spec["linestyle"],
                 )


    plt.legend(["Canonical", "vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    plt.ylabel('% of successful embedding')
    plt.xlabel('# of Embeded requests')
    # plt.show()


    plt.savefig("%d-embedding.pdf" % id, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)
    plt.clf()



def get_display_style(name):
    if name=="none":
        return {'color':'r', 'label':"none", 'linestyle':"solid"}
    elif name=="vhg":
        return {'color':'b', 'label':"vhg", 'linestyle':"solid"}
    elif name=="vcdn":
        return {'color':'y', 'label':"vhg", 'linestyle':"solid"}
    elif name=="all":
        return {'color':'g', 'label':"vhg", 'linestyle':"solid"}

def plot_results_bw(res, init_point, id):

    for key in res.keys():
        spec=get_display_style(key)
        init_value=res[key][0].substrate.get_edges_sum()
        plt.plot([x[0] for x in enumerate(res[key][init_point:])],
                 [100 - x.substrate.get_edges_sum()/init_value*100 for x in res[key][init_point:]],
                 color=spec["color"],
                 label=spec["label"],
                 linestyle=spec["linestyle"],
                 )

    plt.legend(["Canonical", "vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    plt.ylabel('% of Substrate Bandwidth Usage')
    plt.xlabel('# of Embeded Requests')
    # plt.show()
    plt.savefig("%d-edge-capacities.pdf" % id, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)

    plt.clf()


def plotsol():
    edges = []
    nodesdict = {}
    cdn_candidates=[]
    starters_candiates=[]


    with open("CDN.nodes.data", 'r') as f:
        data = f.read()
        for line in data.split("\n"):
            line = line.split("\t")
            if len(line) == 2:
                cdn_candidates.append(line[1])

    with open("starters.nodes.data", 'r') as f:
        data = f.read()
        for line in data.split("\n"):
            line = line.split("\t")
            if len(line) == 2:
              starters_candiates.append(line[1])



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
            matches = re.findall("^x\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                nodesSol.append(matches[0])
                continue
            matches = re.findall("^y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                edgesSol.append(matches[0])
                continue

    with open("substrate.dot", 'w') as f:
        f.write("graph{rankdir=LR;\n\n\n\n subgraph{\n\n\n")

        avgcpu = reduce(lambda x, y: float(x) + float(y), nodesdict.values(), 0.0) / len(nodesdict)


        for node in nodesdict.items():
            if node[0] in starters_candiates:
                color="green1"
            elif node[0] in cdn_candidates:
                color="red1"
            else:
                color = "black"
            f.write("%s [shape=box,color=%s,width=%f,fontsize=15,pos=\"%d,%d\"];\n" % (node[0], color,min(1, float(node[1]) / avgcpu),int(node[0][:2]),int(node[0][-2:])))

        avgbw = [float(edge[2]) for edge in edges]
        avgbw = sum(avgbw) / len(avgbw)

        avgdelay = reduce(lambda x, y: float(x) + float(y[3]), edges, 0.0) / len(edge)
        for edge in edges:
            availbw = float(edge[2])
            # f.write("%s->%s [ label=\"%d\", penwidth=\"%d\", fontsize=20];\n " % (edge[0], edge[1], float(edge[2]), 1+3*availbw/avgbw))
            f.write("%s--%s [  penwidth=\"%d\", fontsize=15,len=2];\n " % (edge[0], edge[1], 3))

        for node in nodesSol:
            if node[1]!="S0":
                f.write("%s--%s[color=red,len=1.5];\n" % node)
                if "VHG" in node[1]:
                    color="azure1"
                elif "vCDN" in node[1]:
                    color="azure3"
                elif "S" in node[1]:
                    color="green"
                else :
                    color="red"

                f.write("%s[shape=circle,fillcolor=%s,style=filled,fontsize=12];\n" % (node[1],color))
        f.write("}")

        f.write("\nsubgraph{\n edge[color=blue3,weight=0];\n")
        for edge in edgesSol:
            if edge[2]!="S0":
                f.write("%s--%s [ style=dashed,label=\"%s-->%s\",fontcolor=blue3 ,fontsize=8,penwidth=1];\n " % (edge))

        f.write("}\n\n")
        f.write("}")


if __name__ == "__main__":
    plotsol()
    file=tempfile.mkstemp(".pdf")[1]
    subprocess.Popen( ["neato", "./substrate.dot" ,"-Tpdf" ,"-o", file]).wait()
    subprocess.Popen(["evince",file]).wait()



