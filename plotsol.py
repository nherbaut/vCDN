#!/usr/bin/env python
import re
	
with open("substrate.dot",'a') as f:
	with open("solutions.data","r") as sol:
		data=sol.read().split("\n")
		nodes=[]
		edges=[]
		for line in data:
			matches=re.findall("x\$(.*)\$([^ \t]+)",line)
			if(len(matches)>0):
				nodes.append(matches[0])
				continue
			matches=re.findall("y\$(.*)\$(.*)\$(.*)\$([^ \t]+)",line)
			if(len(matches)>0):
				edges.append(matches[0])
				continue
		
	
	
	for node in nodes:
		f.write("%s->%s[color=blue];\n"%node)
		f.write("%s[shape=circle,fillcolor=azure3,style=filled];\n"%node[1])
		
	f.write("}")
	
	f.write("\nsubgraph{\n edge[color=blue3];\n")
	for edge in edges:
		f.write("%s->%s [ label=\"%s->%s\",fontcolor=blue3 ];\n " % (edge))
		
	f.write("}\n\n")
	f.write("}")
