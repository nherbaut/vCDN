set N	:= {read "substrate.nodes.data" as "<1s>"};
set NS	:= {read "service.nodes.data" as "<1s>"};

set E := { read "substrate.edges.data" as "<1s,2s>"};
set Et := { <u,v> in N cross N with <v,u> in E};
set ES := { read "service.edges.data" as "<1s,2s>"};
set CDN := {read "CDN.nodes.data" as "<1s,2s>"};
set CDN_LABEL := {read "CDN.nodes.data" as "<1s>"};
set CDN_LINKS := {<i,j> in ES inter (NS cross CDN_LABEL) with i!=j};


set VHG_LABEL := {read "VHG.nodes.data" as "<1s>"};
set VHG_INCOMING_LINKS := {<i,j> in ES inter (NS cross VHG_LABEL) with i!=j};
set VHG_OUTGOING_LINKS := {<i,j> in ES inter (VHG_LABEL cross NS) with i!=j};


set VCDN_LABEL := {read "VCDN.nodes.data" as "<1s>"};
set VCDN_INCOMING_LINKS := {<i,j> in ES inter (NS cross VCDN_LABEL)};



set STARTERS_MAPPING := {read "starters.nodes.data" as "<1s,2s>"};
set STARTERS_LABEL := {read "starters.nodes.data" as "<1s>"};
set STARTERS_OUTGOING_LINKS := {<i,j> in ES inter (STARTERS_LABEL cross NS) with i!=j};
set STARTERS_INCOMING_LINKS := {<i,j> in ES inter (NS cross STARTERS_LABEL ) with i!=j};

set SERVICE_PATHS := {read "service.path.data" as "<1s,2s,3s>"};
set SERVICE_PATHS_DELAY := {read "service.path.delay.data" as "<1s,2n>"};



defset delta(u) := { <v> in N with <u,v> in (E union Et)};
param cpuS[NS] := read "service.nodes.data" as "<1s> 2n";
param cpu[N] := read "substrate.nodes.data" as "<1s> 2n";

param delays[E] := read "substrate.edges.data" as "<1s,2s> 4n";


param bwS[ES] := read "service.edges.data" as "<1s,2s> 3n";
param bw[E] := read "substrate.edges.data" as "<1s,2s> 3n";
param bwt[Et] := read "substrate.edges.data" as "<2s,1s> 3n";
param source := read "starters.nodes.data" as "2s" use 1;
param cdn_count := read "cdnmax.data" as "1n" use 1;
param node1 := read "node1.data" as "1s" use 1;
param node2 := read "node2.data" as "1s" use 1;




var x_cdn[N cross CDN_LABEL ] binary;
var y [(E union Et) cross ES ] binary;
var y_cdn [(E union Et) cross ES ] binary;
var w binary;
var cdns_var [CDN_LABEL] binary;


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

	
		
