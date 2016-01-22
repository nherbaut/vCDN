#!/usr/bin/env python
import argparse
from pygraphml import Graph
from pygraphml import GraphMLParser
import random


parser = argparse.ArgumentParser(description='generate dataset for service chaining')
parser.add_argument('--file',  default="Geant2012.graphml",
                   help='file to read')
                   
parser.add_argument('--start',  type=int,
                   help='starting node')


parser.add_argument('--cdn',  type=int,
                   help='cdn node')
                   
                   
args = parser.parse_args()



parser = GraphMLParser()
#g = parser.parse("Geant2012.graphml")
g = parser.parse(args.file)


if args.start is None:
	users=random.choice(g.nodes()).id
else:
	users=int(args.start)
	

if args.cdn is None:
	cdn=random.choice(g.nodes()).id
else:
	cdn=int(args.cdn)	
	

edges=[(e.node1.id,e.node2.id,e.attributes()["d42"].value) for e in g.edges() if "d42" in e.attributes()]
nodes=set([n.id for n in g.nodes()])
nodesdict={}
for l in nodes:
	
	
	if l in [cdn,users]:
		value=0
	
	else:
		value=random.random()*100
	nodesdict[l]=value

	
with open("substrate.edges.data",'w') as f:
	for l in edges:
		f.write("%s	%s	%lf\n" % (l[0],l[1],float(l[2])))
		

with open("CDN.nodes.data",'w') as f:
	f.write("%s \n" % cdn)

with open("users.nodes.data",'w') as f:
	f.write("%s \n" % users)


with open("substrate.nodes.data",'w') as f:
	for node in nodesdict.items():
		f.write("%s	%lf\n" % (node[0],node[1]))
		
		
with open("substrate.dot",'w') as f:
	f.write("digraph{rankdir=LR;\n\n\n\n subgraph{\n\nedge[dir=none];\n")
	for node in nodesdict.items():
		f.write(str(node[0])+" [shape=box,color=black];\n")
	
	for edge in edges:
		f.write("%s->%s [ label=\"%d\" ];\n " % (edge[0],edge[1],float(edge[2])))
	
	
