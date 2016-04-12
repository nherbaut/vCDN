set N	:= {read "substrate.nodes.data" as "<1s>"};
set NS	:= {read "service.nodes.data" as "<1s>"};

set E := { read "substrate.edges.data" as "<1s,2s>"};
set Et := { <u,v> in N cross N with <v,u> in E};
set ES := { read "service.edges.data" as "<1s,2s>"};


set Path := { read "path.data" as "<1s>"};
set tuplePath :={ <i> in {1..(card(Path)-1)} : <ord(Path,i,1),ord(Path,i+1,1)>};

param cpuS[NS] := read "service.nodes.data" as "<1s> 2n";
param cpu[N] := read "substrate.nodes.data" as "<1s> 2n";

param delays[E] := read "substrate.edges.data" as "<1s,2s> 4n";
param delayst[Et] := read "substrate.edges.data" as "<2s,1s> 4n";
param delaysS[ES] := read "service.edges.data" as "<1s,2s> 4n";


param bwS[ES] := read "service.edges.data" as "<1s,2s> 3n";
param bw[E] := read "substrate.edges.data" as "<1s,2s> 3n";
param bwt[Et] := read "substrate.edges.data" as "<2s,1s> 3n";

param CDN := read "CDN.nodes.data" as "1s" use 1 ;
param starters := "0";



var x[N cross NS] binary;
var y [(E union Et) cross ES] binary;
var w binary;


#minimize cost: 	
#				sum <a,b> in tuplePath:(
#					sum <u,v> in E:
#						(y[u,v,a,b] * delays[u,v] )+
#					sum <u,v> in Et:
#						(y[u,v,a,b] * delayst[u,v])) ;

#maximize cost:
#				sum <a,b> in tuplePath:(
#					sum <u,v> in E:
#						((bw[u,v]-(y[u,v,a,b] * bwS[a,b] ))/(0.1+bw[u,v]))+
#					sum <u,v> in Et:
#						((bw[v,u]-(y[u,v,a,b] * bwS[a,b] ))/(0.1+bw[v,u])));
						

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
   forall <u,v> in E:
		forall <i,j> in ES:
			y[u,v,i,j]*delays[u,v] <= delaysS[i,j];



subto flowconservation:
   forall <i,j> in {<i,j> in ES with i != j}:
      forall <u> in N:
         sum<v> in {<v> in N with <u,v> in (E union Et)}: (y[u, v, i, j] - y[v, u, i,j]) == x[u,i]-x[u,j];
         
subto noloop:
	forall <i,j> in {<i,j> in ES with i != j}:
		forall <u,v> in (E union Et):
			y[u, v, i, j] + y[v, u, i,j] <= 1;
		
		
subto CDNIn7:
    x[CDN,"CDN"]==1;
    
subto startisstart:
    x[starters,"S"]==1;
    
subto startisstart2:
    sum<v> in NS: x[starters,v]==1;
