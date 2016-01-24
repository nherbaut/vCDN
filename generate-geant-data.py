#!/usr/bin/env python
import argparse

import numpy as np
from pygraphml import GraphMLParser

parser = argparse.ArgumentParser(description='generate dataset for service chaining')
parser.add_argument('--file', default="Geant2012.graphml",
                    help='file to read')

parser.add_argument('--start', type=int,
                    help='starting node')

parser.add_argument('--cdn', type=int,
                    help='cdn node')

parser.add_argument('--seed', type=int,
                    help='random seed')

parser.add_argument('--refresh', dest='refresh', action='store_true')
parser.set_defaults(refresh=False)

args = parser.parse_args()

parser = GraphMLParser()
# g = parser.parse("Geant2012.graphml")
g = parser.parse(args.file)

print(args.seed)

if args.seed is None:
    rs = np.random.RandomState(0)
else:
    rs = np.random.RandomState(seed=args.seed)

if args.start is None:
    users = rs.choice(g.nodes()).id
else:
    users = int(args.start)

if args.cdn is None:
    cdn = rs.choice(g.nodes()).id
else:
    cdn = int(args.cdn)

# edges = [(e.node1.id, e.node2.id, e.attributes()["d42"].value,max(5+np.random.normal(10, 5, 1)[0],0)) for e in g.edges() if "d42" in e.attributes()]
edges = [(e.node1.id, e.node2.id, max(rs.normal(100, 60, 1)[0], 0), max(rs.normal(10, 5, 1)[0], 0)) for e in g.edges()]
nodes = set([n.id for n in g.nodes()])
nodesdict = {}
for l in nodes:

    if l in [cdn, users]:
        value = 0
    else:
        value = max(rs.normal(10, 60, 1)[0], 0)
    nodesdict[l] = value

if args.refresh:
    with open("substrate.edges.data", 'w') as f:
        for l in edges:
            f.write("%s\t%s\t%lf\t%lf\n" % (l[0], l[1], float(l[2]), l[3]))

    with open("CDN.nodes.data", 'w') as f:
        f.write("%s \n" % cdn)

    with open("starters.nodes.data", 'w') as f:
        f.write("%s \n" % users)

    with open("substrate.nodes.data", 'w') as f:
        for node in nodesdict.items():
            f.write("%s\t%lf\n" % (node[0], node[1]))
