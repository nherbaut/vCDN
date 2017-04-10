# Build/dependencies

we provide a way to build docker images for the optimization library. To build the image type the following command (takes 1h to build)

```
sudo docker build -f ./optim.Dockerfile -t nherbaut/simuservice .
```

if you don't want to build, just get our latest image from the docker hub

```
sudo docker pull nherbaut/simuservice:latest .
```



# Running

We assumed that you have retreived the latest version of our docker image. To run the tool, just run the docker image.


## Usage

### Get help

```
docker run  nherbaut/simuservice --help
```


### Get Running the optimization algorithm on Geant for 2 nodes

```
sudo docker run nherbaut/simuservice --start 14  --cdn 38 --vhg 1 --vcdn 1 --sourcebw 100000000 --topo=file,Geant2012.graphml,10000
```

if we do that, the results are contained in a file within the container. To access it, you can go in the stopped container, OR launch the container so that the result will be written on the host file system:

```
sudo docker run -v $PWD/output:/opt/girafe/results nherbaut/simuservice --start 14  --cdn 38 --vhg 1 --vcdn 1 --sourcebw 100000000 --topo=file,Geant2012.graphml,10000
```

In that case, the $PWD/output folder contain the following files
```
nherbaut@nherbaut-laptop:~/workspace/simuservice$ ls -l ./output/
total 12
-rw-r--r-- 1 root root  628 avril 11 00:02 mapping.json
-rw-r--r-- 1 root root   16 avril 11 00:02 price.data
-rw-r--r-- 1 root root 3440 avril 11 00:02 substrate.json
```

* price.data contain the best price for the requested embedding
* mapping.json contains the mapping between the service graph and the topology
* substrate.json contains the original topology

### Get the Substrate topology info in the STDOUT

It could be convevient to get the results right in the stdout (that's what we use with girafe-web). To do that, just specify the **--json** flag to get the results (--base64 will encore the results in base64 for easy HTTP transfert)


```
nherbaut@nherbaut-laptop:~/workspace/simuservice$ sudo docker run nherbaut/simuservice --start 14  --cdn 38 --vhg 1 --vcdn 1 --sourcebw 100000000 --topo=file,Geant2012.graphml,10000 --json
{"mapping": {"directed": false, "multigraph": false, "nodes": [{"mapping": "14", "bandwidth": 100000000.0, "id": "VHG1", "cpu": 41.0}, {"mapping": "14", "bandwidth": 35000000.0, "id": "VCDN1", "cpu": 20.035}, {"mapping": "38", "bandwidth": 65000000.0, "id": "CDN1", "cpu": 0.0}, {"mapping": "14", "bandwidth": 100000000.0, "id": "S1", "cpu": 0.0}], "links": [{"source": 0, "mapping": [["12", "15"], ["15", "28"], ["29", "38"], ["3", "29"], ["3", "4"], ["12", "14"], ["4", "28"]], "delay": 27.014339791393933, "target": 2, "bandwith": 65000000.0}], "graph": {}}, "price": {"vcdn_count": 1, "total_price": 4487.9, "vhg_count": 1}}nherbaut@nherbaut-laptop:~/workspace/simuservice$ 

```

In that case, you will need several runs to get all the infos (mapping, original substrate...)


## Picking the start nodes for vCDN at random 

instead of specifying the **--start** and **--cdn** flags, you can have them selected at random.

```
sudo docker run nherbaut/simuservice --start "RAND(1,5)"  --cdn "RAND(2,2)" --vhg 1 --vcdn 1 --sourcebw 100000000 --topo=file,Geant2012.graphml,10000
```
here, between 1 and 5 start nodes will be selected randomly and 2 cdn nodes will be selected randomly on the substrate graph.
