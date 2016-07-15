# What's in?

./offline is the service mapping algo/simulation
./sdn is the online management using mininet/sdn


# dependencies

```
cycler==0.10.0
decorator==4.0.9
haversine==0.4.5
matplotlib==1.5.1
networkx==1.11
numpy==1.11.0
pygraphml==2.0
pyparsing==2.1.1
python-dateutil==2.5.3
pytz==2016.4
scipy==0.17.0
six==1.10.0
```

# RUNTIME

batch simulation: 
```
python -m offline.tools.simu
```


1 step simulation:
```
python -m offline.tools.step
```

power law (Holme and Kim algorithm) args: n,m,p,s with n = the number of nodes, m = the number of random edges to add for each new node, p=Probability of adding a triangle after adding a random edge, s = seed (int)
```
python -m offline.tools.step --topo powerlaw,100,1,0.5,1
```
ErdosRenyi args: n,p,s with n = the number of nodes, p = the probability of edge creation, s = the seed (int)

```
python -m offline.tools.dstep --start 1 2 --topo erdos_renyi,30,0.1,3 --cdn 9 10
```


from graphfml file 


```
python -m offline.tools.dstep --start 1 2 --topo file,Geant2012.graphml --cdn 9 10
```



1 step simulation, deterministic:
```
python -m offline.tools.dstep --start 0101 0505 --cdn  0504 --vhg 2 --grid 5x5
```

1 step simulation, deterministic, topo only:
```
python -m offline.tools.dstep --topo  --grid 5x5
```

Optimal Solution:
```
python -m offline.tools.ostep --start 1 2 --topo erdos_renyi,30,0.1,3 --cdn 9 10
```




plotting with pdf viewer:
```
python -m offline.tools.plotting --view
```



# Docker image

coming soon
