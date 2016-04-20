set N	:= {read "substrate.nodes.data" as "<1s>"};
set NS	:= {read "service.nodes.data" as "<1s>"};

set E := { read "substrate.edges.data" as "<1s,2s>"};
set Et := { <u,v> in N cross N with <v,u> in E};
set ES := { read "service.edges.data" as "<1s,2s>"};



defset delta(u) := { <v> in N with <u,v> in (E union Et)};

param cpuS[NS] := read "service.nodes.data" as "<1s> 2n";
param cpu[N] := read "substrate.nodes.data" as "<1s> 2n";

param delays[E] := read "substrate.edges.data" as "<1s,2s> 4n";
param delayst[Et] := read "substrate.edges.data" as "<2s,1s> 4n";
param delaysS[ES] := read "service.edges.data" as "<1s,2s> 4n";


param bwS[ES] := read "service.edges.data" as "<1s,2s> 3n";
param bw[E] := read "substrate.edges.data" as "<1s,2s> 3n";
param bwt[Et] := read "substrate.edges.data" as "<2s,1s> 3n";

param CDN := read "CDN.nodes.data" as "1s" use 1 ;
set starters := {read "starters.nodes.data" as "<1s,2s>"};
param source := read "starters.nodes.data" as "2s" use 1;



var x[N cross NS] binary;
var y [(E union Et) cross ES] binary;
var w binary;



maximize cost:
			    sum <u,v> in E:
					((bw[u,v]-sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] ))/(bw[u,v]))+
				sum <u,v> in Et:
				    ((bw[v,u]-sum <i,j> in ES:(y[u,v,i,j] * bwS[i,j] ))/(bw[v,u]));


#maximize cost:
#			    sum <u> in N:(
#			      cpu[u]-sum<i> in NS:(x[u,i]*cpuS[i])/cpu[u]);



subto fc:
	forall <j> in NS:
		sum<i> in N: x[i,j]==1;
		

subto popRes:
	forall <i> in N:
		sum<j> in NS: x[i,j]*cpuS[j] <= cpu[i];
		
		
subto bwSubstrate:
   forall <u,v> in E:
       sum<i,j> in ES : (y[u,v,i,j]+y[v,u,i,j]) * bwS[i,j] <= bw[u,v];
       
subto bwtSubstrate:
   forall <u,v> in Et:
       sum<i,j> in ES : (y[u,v,i,j]+y[v,u,i,j]) * bwS[i,j] <= bwt[u,v];


subto delaySubstrate:
   	forall <i,j> in ES:
   	    sum <u,v> in E:
			y[u,v,i,j]*delays[u,v] <= delaysS[i,j];



subto flowconservation:
   forall <i,j> in {<i,j> in ES with i != j}:
      forall <u> in N:
         sum<v> in {<v> in N with <u,v> in (E union Et)}: (y[u, v, i, j] - y[v, u, i,j]) == x[u,i]-x[u,j];
         
subto noloop:
	forall <i,j> in {<i,j> in ES with i != j}:
		forall <u,v> in (E union Et):
			y[u, v, i, j] + y[v, u, i,j] <= 1;
			
subto noBigloop:
	forall <i,j> in {<i,j> in ES with i != j}:
		forall <u> in N:
			sum <v> in delta(u):
			  y[u,v,i,j] <= 1;
		
		
		
subto cdn2cdn:
    x[CDN,"CDN"]==1;
    
subto startsource:
    x[source,"S0"]==1;
    
subto sources:
    forall <name,id> in starters:
        x[id,name]==1;
