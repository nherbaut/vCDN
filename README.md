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

1 step simulation, deterministic:
```
python -m offline.tools.dstep --start 0101 0505 --cdn  0504 --vhg 2 --grid 5x5
```

1 step simulation, deterministic, topo only:
```
python -m offline.tools.dstep --topo  --grid 5x5
```


plotting with pdf viewer:
```
python -m offline.tools.plotting --view
```



# Docker image

```
docker run -it -v $(pwd)/offline/results:/opt/simuservice/offline/results/ dngroup/simuservice python -m offline.tools.dstep --start 0103 0303 --cdn  0301 --sla_delay 30  --grid 3x3 --sourcebw 1000000000  --vcdnratio 0.35
docker run -it -v $(pwd)/offline/results:/opt/simuservice/offline/results/ dngroup/simuservice python -m offline.tools.plotting --svg
```
build image

```
docker build -t dngroup/simuservice .
```


# Docker network Simulator

package needed

```
sudo apt-get install -y openvswitch-common
```
RUN

```
docker run -ti --rm=true --net=host --pid=host --privileged=true -v '/var/run/docker.sock:/var/run/docker.sock' dngroup/minicker /bin/bash
```
