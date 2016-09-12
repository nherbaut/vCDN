#!/usr/bin/env python
import time
import multiprocessing
import numpy as np
from docker import Client
thread_per_simu=2
cli = Client(base_url='unix://var/run/docker.sock')
containers = []
for price in list((i * 10 ** exp for exp in range(-2, 10) for i in range(5, 6))):
    for discount in np.arange(0.3, 0.55, 0.02):
        while len(cli.containers()) >= multiprocessing.cpu_count()/thread_per_simu:
            time.sleep(1)
        print("launching %lf, %lf"%(price,discount))
        container = cli.create_container(image='nherbaut/simu-time',
                                         command="bash -c './bootstrap.sh > /dev/null && ./start.py -l DEBUG -i %lf -d %lf -t %d  >> /opt/simuservice/out/res.txt && echo hn:$HOSTNAME >> /opt/simuservice/out/res.txt && mkdir /opt/simuservice/out/$HOSTNAME && cp /opt/simuservice/*.svg /opt/simuservice/out/$HOSTNAME'" % (
                                             price, discount, thread_per_simu),
                                         host_config=cli.create_host_config(binds=[
                                             '/home/ubuntu/res:/opt/simuservice/out',

                                         ])

                                         )
        cli.start(container=container.get("Id"))
        print("new containers %s launched" % container.get("Id"))

