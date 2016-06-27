set N	:= {read "../results/substrate.nodes.data" as "<1s>"};

set E := { read "../results/substrate.edges.data" as "<1s,2s>"};
set Et := { <u,v> in N cross N with <v,u> in E};
param delays[E] := read "../results/substrate.edges.data" as "<1s,2s> 4n";


param node1 := read "../results/node1.data" as "1s" use 1;
param node2 := read "../results/node2.data" as "1s" use 1;



defset dminus(v) := {<i,v> in  (E union Et)};
defset dplus(v) := {<v,j> in (E union Et)};
var x[E union Et] binary;

minimize cost: sum<i,j> in (E): delays[i,j] * x[i,j] + sum<i,j> in (Et): delays[j,i] * x[i,j];


do forall <i,j> in dplus(node1) do print i," ",j;

subto fc:
	forall <v> in N - {node1,node2}:
		sum<i,v> in dminus(v): x[i,v] == sum<v,i> in dplus(v): x[v,i];

subto df:
	sum<s,i> in dplus(node1): x[s,i] == 1;

subto sdfdf:
	sum<s,i> in dplus(node2): x[s,i] == 0;

subto sdf:
	sum<s,i> in dminus(node2): x[s,i] == 1;

subto sdfs:
	sum<s,i> in dminus(node1): x[s,i] == 0;

	
		
