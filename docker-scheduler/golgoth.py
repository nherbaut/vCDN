#!/usr/bin/env python
from docker import Client
import numpy as np
import time
cli = Client(base_url='unix://var/run/docker.sock')
containers=[]
for price in list((i*10**exp for exp in range(-2, 10) for i in range(5,6))):
  for discount in np.arange(0.3,0.55,0.05):
	while len(cli.containers())>4:
	  time.sleep(1)
	container = cli.create_container(image='nherbaut/simu-time', command="bash -c './bootstrap.sh > /dev/null && ./start.py -l DEBUG -i %lf -d %lf'"%(price,discount))
	cli.start(container=container.get("Id"))
        print("new containers %s launched"%container.get("Id"))
