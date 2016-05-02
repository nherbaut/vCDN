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




var x[N cross NS ] binary;
var x_cdn[N cross CDN_LABEL ] binary;
var y [(E union Et) cross ES ] binary;
var y_cdn [(E union Et) cross ES ] binary;
var w binary;
var cdns_var [CDN_LABEL] binary;


#minimize cost:
#    sum <u,v> in E union Et:
#		sum <i,j> in ES:y[u,v,i,j] * bwS[i,j];

maximize cost:
                        sum <u,v> in E:
                                    ((bw[u,v]-sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] ))/(bw[u,v]))+
                            sum <u,v> in Et:
                                ((bw[v,u]-sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] ))/(bw[v,u]));


subto everyNodeIsMapped:
	forall <j> in NS\CDN_LABEL:
		sum<i> in N: x[i,j]==1;


subto popRes:
	forall <i> in N:
		sum<j> in NS: x[i,j]*cpuS[j] <= cpu[i];

		
subto bwSubstrate:
   forall <u,v> in E:
       sum<i,j> in ES: (y[u,v,i,j]+y[v,u,i,j]) * bwS[i,j] <= bw[u,v];




subto E2EdelayConstraint:
  forall <service,delay> in SERVICE_PATHS_DELAY:
    forall <k,i,j> in {<k,i,j>  in SERVICE_PATHS with k==service}:
     (sum <u,v> in E:y[u,v,i,j]*delays[u,v] + sum <u,v> in Et: y[u,v,i,j]*delays[v,u])<= delay;



subto flowconservation:
   forall <i,j> in {<i,j> in ES\CDN_LINKS }:
      forall <u> in N:
         sum<v> in {<v> in N with <u,v> in (E union Et)}: (y[u, v, i, j] - y[v, u, i,j]) == x[u,i]-x[u,j];


subto noloop:
	forall <i,j> in {<i,j> in ES  with i != j}:
		forall <u,v> in (E union Et):
			y[u, v, i, j] + y[v, u, i,j] <= 1;
			
subto noBigloop:
	forall <i,j> in {<i,j> in ES  with i != j}:
		forall <u> in N:
			sum <v> in delta(u):
			  y[u,v,i,j] <= 1;
		
		
		

subto startsource:
    x[source,"S0"]==1;
    
subto sources:
    forall <name,id> in STARTERS_MAPPING:
        x[id,name]==1;

subto only1CDN:
  sum <i> in (CDN_LABEL) : cdns_var[i] ==cdn_count;

subto cdnToNode:
	forall <i,j> in CDN:
		x[j,i]==cdns_var[i];

subto flowconservation_cdn:
   forall <i,j> in {<i,j> in CDN_LINKS  with i != j}:
      forall <u> in N:
         sum<v> in {<v> in N with <u,v> in (E union Et)}: (y[u, v, i, j] - y[v, u, i,j]) *cdns_var[j]==( (x[u,i]-x[u,j])*cdns_var[j]);

subto bwSubstrate_cdn:
   forall <u,v> in E:
       sum<i,j> in CDN_LINKS: (y[u,v,i,j]+y[v,u,i,j]) * bwS[i,j]/cdn_count <= bw[u,v];

subto bwtSubstrate_cdn:
   forall <u,v> in Et:
       sum<i,j> in CDN_LINKS: (y[u,v,i,j]+y[v,u,i,j]) * bwS[i,j]/cdn_count <= bwt[u,v];