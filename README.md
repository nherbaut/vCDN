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
docker run  nherbaut/simuservice --help
```

