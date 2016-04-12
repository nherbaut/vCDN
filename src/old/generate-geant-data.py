#!/usr/bin/env python
import argparse

import numpy as np
from haversine import haversine
from pygraphml import GraphMLParser


def get_delay(node1, node2):
    return haversine((float(node1.attributes()["d29"].value),float( node1.attributes()["d32"].value)),
                     (float(node2.attributes()["d29"].value), float(node2.attributes()["d32"].value))) / (299.300 * 0.6)


def isOK(node1, node2):
    try:
        get_delay(node1,node2)
    except:
        return False
    return True

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

nodes = {n.id: n for n in g.nodes()}
edges = [(e.node1.id, e.node2.id, float(e.attributes()["d42"].value),
          get_delay(nodes[e.node1.id], nodes[e.node2.id]))
         for e in g.edges() if "d42" in e.attributes() and  isOK(nodes[e.node1.id], nodes[e.node2.id])]

#for which we have all the data
valid_nodes=list(set([e[0] for e in edges]+[e[1] for e in edges]))
# edges = [(e.node1.id, e.node2.id, max(rs.normal(100, 30, 1)[0], 0), max(rs.normal(10, 5, 1)[0], 0)) for e in g.edges()]






nodes = set([n.id for n in g.nodes() if n.id in valid_nodes])
nodesdict = {}

print valid_nodes

if args.start is None:
    users = rs.choice(valid_nodes)
else:
    users = int(args.start)

if args.cdn is None:
    cdn = rs.choice(valid_nodes)
else:
    cdn = int(args.cdn)


for l in nodes:
    if l in [cdn, users]:
        value = 0
    else:
        #value = max(rs.normal(10, 60, 1)[0], 0)
        value = max(rs.normal(50, 30, 1)[0], 0)
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




