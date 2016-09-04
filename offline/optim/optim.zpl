set N	:= {read "../results/substrate.nodes.data" as "<1s>"};
set NS	:= {read "../results/service.nodes.data" as "<1s>"};

set E := { read "../results/substrate.edges.data" as "<1s,2s>"};
set Et := { <u,v> in N cross N with <v,u> in E};
set ES := { read "../results/service.edges.data" as "<1s,2s>"};
set CDN := {read "../results/CDN.nodes.data" as "<1s,2s>"};
set CDN_LABEL := {read "../results/CDN.nodes.data" as "<1s>"};
set CDN_LINKS := {<i,j> in ES inter (NS cross CDN_LABEL) with i!=j};
set CDN_MAPPING := {read "../results/CDN.nodes.data" as "<1s,2s>"};

set VHG_LABEL := {read "../results/VHG.nodes.data" as "<1s>"};
set VHG_INCOMING_LINKS := {<i,j> in ES inter (NS cross VHG_LABEL) with i!=j};
set VHG_OUTGOING_LINKS := {<i,j> in ES inter (VHG_LABEL cross NS) with i!=j};


set VCDN_LABEL := {read "../results/VCDN.nodes.data" as "<1s>"};
set VCDN_INCOMING_LINKS := {<i,j> in ES inter (NS cross VCDN_LABEL)};



set STARTERS_MAPPING := {read "../results/starters.nodes.data" as "<1s,2s>"};
set STARTERS_LABEL := {read "../results/starters.nodes.data" as "<1s>"};
set STARTERS_OUTGOING_LINKS := {<i,j> in ES inter (STARTERS_LABEL cross NS) with i!=j};
set STARTERS_INCOMING_LINKS := {<i,j> in ES inter (NS cross STARTERS_LABEL ) with i!=j};

set SERVICE_PATHS := {read "../results/service.path.data" as "<1s,2s,3s>"};
set SERVICE_PATHS_DELAY := {read "../results/service.path.delay.data" as "<1s,2n>"};



defset delta(u) := { <v> in N with <u,v> in (E union Et)};
param cpuS[NS] := read "../results/service.nodes.data" as "<1s> 2n";
param cpu[N] := read "../results/substrate.nodes.data" as "<1s> 2n";

param delays[E] := read "../results/substrate.edges.data" as "<1s,2s> 4n";


param bwS[ES] := read "../results/service.edges.data" as "<1s,2s> 3n";
param bw[E] := read "../results/substrate.edges.data" as "<1s,2s> 3n";
param bwt[Et] := read "../results/substrate.edges.data" as "<2s,1s> 3n";
param source := read "../results/starters.nodes.data" as "2s" use 1;



param cpuCost_vHG := read "../pricing/vmg/pricing_for_one_instance.properties" as "1n" use 1;
param cpuCost_vCDN := read "../pricing/cdn/pricing_for_one_instance.properties" as "1n" use 1;

param netCost := read "../pricing/net.cost.data" as "1n" use 1;

var x[N cross NS ] binary;
var x_cdn[N cross CDN_LABEL ] binary;
var y [(E union Et) cross ES ] binary;
var y_cdn [(E union Et) cross ES ] binary;
var w binary;



minimize cost:
    sum <u,v> in E union Et:(
		sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] * netCost)) +
		sum<vhg> in VHG_LABEL:(cpuCost_vHG*cpuS[vhg])+
		sum<vcdn> in VCDN_LABEL:(cpuCost_vCDN*cpuS[vcdn]);



#maximize cost:
#                        sum <u,v> in E:
#                                    ((bw[u,v]-sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] ))/(bw[u,v]))+
#                            sum <u,v> in Et:
#                                ((bw[v,u]-sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] ))/(bw[v,u]));


subto everyNodeIsMapped:
	forall <j> in NS:
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
		
		




subto sources:
    forall <name,id> in STARTERS_MAPPING:
        x[id,name]==1;

subto cdn:
    forall <name,id> in CDN_MAPPING:
        x[id,name]==1;



subto flowconservation_cdn:
   forall <i,j> in {<i,j> in CDN_LINKS  with i != j}:
      forall <u> in N:
         sum<v> in {<v> in N with <u,v> in (E union Et)}: (y[u, v, i, j] - y[v, u, i,j]) ==( (x[u,i]-x[u,j]));

subto bwSubstrate_cdn:
   forall <u,v> in E:
       sum<i,j> in CDN_LINKS: (y[u,v,i,j]+y[v,u,i,j]) * bwS[i,j] <= bw[u,v];

subto bwtSubstrate_cdn:
   forall <u,v> in Et:
       sum<i,j> in CDN_LINKS: (y[u,v,i,j]+y[v,u,i,j]) * bwS[i,j] <= bwt[u,v];