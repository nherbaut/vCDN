#!/usr/bin/env python
import re

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
    f.write("digraph{rankdir=LR;\n\n\n\n subgraph{\n\nedge[dir=none];\n")

    avgcpu = reduce(lambda x,y: float(x)+float(y),nodesdict.values(),0.0)/len(nodesdict)

    for node in nodesdict.items():
        f.write("%s [label=%2.2f,shape=box,color=black,width=%f];\n"%(node[0],float(node[1]),float(node[1])/avgcpu))

    avgbw = [float(edge[2]) for edge in edges]
    avgbw = sum(avgbw) / len(avgbw)

    avgdelay = reduce(lambda x,y: float(x)+float(y[3]),edges,0.0)/len(edge)
    for edge in edges:
        availbw = float(edge[2])
        f.write("%s->%s [ label=\"%d\", penwidth=\"%d\", minlen=\"%d\"];\n " % (edge[0], edge[1], float(edge[2]), 1+3*availbw/avgbw,2*(1+float(edge[3])/avgdelay)))

    for node in nodesSol:
        f.write("%s->%s[color=red];\n" % node)
        f.write("%s[shape=circle,fillcolor=azure3,style=filled];\n" % node[1])

    f.write("}")

    f.write("\nsubgraph{\n edge[color=blue3,weight=0];\n")
    for edge in edgesSol:
        f.write("%s->%s [ label=\"%s-%s\",fontcolor=blue3 ];\n " % (edge))

    f.write("}\n\n")
    f.write("}")
