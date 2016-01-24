#!/usr/bin/env python
import re

edges = []
nodesdict = {}
with open("substrate.edges.data", 'r') as f:
    data=f.read()
    for line in data.split("\n"):
        line = line.split("\t")
        if len(line) == 4:
            edges.append(line )

with open("substrate.nodes.data", 'r') as f:
    data=f.read()
    for line in data.split("\n"):

        line = line.split("\t")
        if (len(line) == 2):
            nodesdict[line[0]] = line[1]

with open("substrate.dot", 'w') as f:
    f.write("digraph{rankdir=LR;\n\n\n\n subgraph{\n\nedge[dir=none];\n")
    for node in nodesdict.items():
        f.write(str(node[0]) + " [shape=box,color=black];\n")

    for edge in edges:
        f.write("%s->%s [ label=\"%d\" ];\n " % (edge[0], edge[1], float(edge[2])))

with open("substrate.dot", 'a') as f:
    with open("solutions.data", "r") as sol:
        data = sol.read().split("\n")
        nodes = []
        edges = []
        for line in data:
            matches = re.findall("x\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                nodes.append(matches[0])
                continue
            matches = re.findall("y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                edges.append(matches[0])
                continue

    for node in nodes:
        f.write("%s->%s[color=red];\n" % node)
        f.write("%s[shape=circle,fillcolor=azure3,style=filled];\n" % node[1])

    f.write("}")

    f.write("\nsubgraph{\n edge[color=blue3,weight=0];\n")
    for edge in edges:
        f.write("%s->%s [ label=\"%s-%s\",fontcolor=blue3 ];\n " % (edge))

    f.write("}\n\n")
    f.write("}")
