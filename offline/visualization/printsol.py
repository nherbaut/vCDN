#!/usr/bin/env python
import re
from functools import reduce

edges = []
nodesdict = {}
with open("substrate.edges.data", 'r') as f:
    data = f.read()
    # print data
    for line in data.split("\n"):
        line = line.split("\t")
        if len(line) == 4:
            edges.append(line)

with open("substrate.nodes.data", 'r') as f:
    data = f.read()
    for line in data.split("\n"):

        line = line.split("\t")
        if len(line) == 2:
            nodesdict[line[0]] = line[1]

with open("solutions.data", "r") as sol:
    data = sol.read()
    if "infeasible" in data:
        pass
    else:
        data = data.split("\n")
    nodesSol = []
    edgesSol = []
    for line in data:
        matches = re.findall("x\$(.*)\$([^ \t]+)", line)
        if len(matches) > 0:
            nodesSol.append(matches[0])
            continue
        matches = re.findall("y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
        if len(matches) > 0:
            edgesSol.append(matches[0])
            continue

with open("substrate.dot", 'w') as f:
    f.write("digraph{rankdir=LR;\n\n\n\n subgraph{\n\n\n")

    avgcpu = reduce(lambda x, y: float(x) + float(y), list(nodesdict.values()), 0.0) / len(nodesdict)

    for node in list(nodesdict.items()):
        f.write("\"%s\" [shape=box,color=black,width=%f,fontsize=20];\n" % (node[0], min(1, float(node[1]) / avgcpu)))

    avgbw = [float(edge[2]) for edge in edges]
    avgbw = sum(avgbw) / len(avgbw)

    avgdelay = reduce(lambda x, y: float(x) + float(y[3]), edges, 0.0) / len(edge)
    for edge in edges:
        availbw = float(edge[2])
        f.write("\"%s\"->\"%s\" [  penwidth=\"%d\", fontsize=20, id=\"%s--%s\"];\n " % (
            edge[0], edge[1], 3, edge[0], edge[1],))

    for node in nodesSol:
        f.write("\"%s\"->\"%s\"[color=red, id=\"%s--%s\"];\n" % (node, node))
        f.write("\"%s\"[shape=circle,fillcolor=azure3,style=filled,fontsize=24];\n" % node[1])

    f.write("}")

    f.write("\nsubgraph{\n edge[color=blue3,weight=0];\n")
    for edge in edgesSol:
        f.write(
            "\"%s\"->\"%s\" [ style=dashed,label=\"%s-->%s\",id=\"%s-->%s\",fontcolor=blue3 ,fontsize=20,penwidth=3];\n " % (
                edge))

    f.write("}\n\n")
    f.write("}")
