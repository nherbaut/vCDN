set N	:= {read "substrate.nodes.data" as "<1s>"};
set NS	:= {read "service.nodes.data" as "<1s>"};

set E := { read "substrate.edges.data" as "<1s,2s>"};
set Et := { <u,v> in N cross N with <v,u> in E};
set ES := { read "service.edges.data" as "<1s,2s>"};

set CDN_ASSIGNED := {read "CDN.nodes.data" as "<1s,2s>"};
set CDN := {read "CDN.nodes.data" as "<1s>"};
set CDN_ES := {<i,j> in ES inter (NS cross CDN) with i!=j};
set VHG := {read "VHG.nodes.data" as "<1s>"};
set VHG_ES := {<i,j> in ES inter (NS cross VHG) with i!=j};
set VCDN := {read "VCDN.nodes.data" as "<1s>"};
set VCDN_ES := {<i,j> in ES inter (NS cross VCDN) with i!=j};
set S := {read "starters.nodes.data" as "<1s>"};
set S_ASSIGNED := {read "starters.nodes.data" as "<1s,2s>"};
set S_ES := {<i,j> in ES inter (NS cross S) with i!=j};

set origin := { "S0" };

#do forall <i,j> in S_ES do print i," ",j;
#do forall <i,j> in VHG_ES do print i," ",j;
#do forall <i,j> in VCDN_ES do print i," ",j;
#do forall <i,j> in CDN_ES do print i," ",j;


defset delta(u) := { <v> in N with <u,v> in (E union Et)};

param cpuS[NS] := read "service.nodes.data" as "<1s> 2n";
param cpu[N] := read "substrate.nodes.data" as "<1s> 2n";

param delays[E] := read "substrate.edges.data" as "<1s,2s> 4n";
param delayst[Et] := read "substrate.edges.data" as "<2s,1s> 4n";
param delaysS[ES] := read "service.edges.data" as "<1s,2s> 4n";



param bwS[ES] := read "service.edges.data" as "<1s,2s> 3n";
param bw[E] := read "substrate.edges.data" as "<1s,2s> 3n";
param bwt[Et] := read "substrate.edges.data" as "<2s,1s> 3n";
param source := read "starters.nodes.data" as "2s" use 1;
param cdn_count := read "cdnmax.data" as "1n" use 1;
param cdnratio := 0.65;



var x[N cross NS ] binary;
var x_cdn[N cross CDN ] binary;
var y [(E union Et) cross ES ] binary;
var y_cdn [(E union Et) cross ES ] binary;
var w binary;
var cdns_var [CDN] binary;
var rho[ES] binary;
var mu[NS] binary;
var gamma[VHG union VCDN] binary;


maximize cost:
			    sum <u,v> in E:
					((bw[u,v]-sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] ))/(bw[u,v]))+
				sum <u,v> in Et:
				    ((bw[v,u]-sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] ))/(bw[v,u]));



subto noVHGIfNolinkToVHGVCDN:
    forall <j> in VHG union VCDN:
       gamma[j] == sum <a,b> in {<aa,bb> in ES with bb==j}: rho[a,b];

subto mappingVHGVCDN:
	forall <j> in VHG union VCDN:
		sum<u> in N: x[u,j] == gamma[j];



subto oneCDNperVHG:
   forall <vhg> in VHG:
     sum <vv,cdn> in {<vv,j> in CDN_ES with vv==vhg}: rho[vv,cdn]<=1;

subto onevCDNperVHG:
   forall <vhg> in VHG:
     sum <vv,vcdn> in {<vv,j> in VCDN_ES with vv==vhg}: rho[vv,vcdn]<=1;

subto oneVHGperSource:
   forall <s> in S:
     sum <i,j> in {<i,j> in ES with i==s}: rho[i,j]==1;

subto rhoSource:
   forall <i,j> in S_ES: rho[i,j]==1;





subto flowconservation:
   forall <i,j> in {<i,j> in ES\CDN_ES  with i != j}:
      forall <u> in N:
         sum<v> in {<v> in N with <u,v> in (E union Et)}:
                    (y[u, v, i, j] - y[v, u, i,j]) == x[u,i]-x[u,j];

subto flowconservation_cdn:
   forall <i,j> in {<i,j> in CDN_ES  with i != j}:
      forall <u> in N:
         sum<v> in {<v> in N with <u,v> in (E union Et)}: (y[u, v, i, j] - y[v, u, i,j]) *cdns_var[j]==( (x[u,i]-x[u,j])*cdns_var[j]);

subto startsource:
    forall <o> in origin:
        x[source,o]==1;

subto sources:
    forall <name,id> in S_ASSIGNED:
        x[id,name]==1;

subto onlyXCDN:
  sum <i> in (CDN) :
    cdns_var[i] ==cdn_count;

subto cdnToNode:
	forall <i,j> in CDN_ASSIGNED:
		x[j,i]==cdns_var[i];


subto popRes:
	forall <i> in N:
    	sum<j> in NS: x[i,j]*cpuS[j] <= cpu[i];


subto noloop:
	forall <i,j> in {<i,j> in ES  with i != j}:
		forall <u,v> in (E union Et):
			y[u, v, i, j] + y[v, u, i,j] <= 1;

subto noBigloop:
	forall <i,j> in {<i,j> in ES  with i != j}:
		forall <u> in N:
			sum <v> in delta(u):
			  y[u,v,i,j] <= 1;


