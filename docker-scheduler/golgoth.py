#!/usr/bin/env python
import time

import numpy as np
from docker import Client

cli = Client(base_url='unix://var/run/docker.sock')
containers = []
for price in list((i * 10 ** exp for exp in range(-2, 10) for i in range(5, 6))):
    for discount in np.arange(0.3, 0.55, 0.05):
        while len(cli.containers()) >= 3:
            time.sleep(1)
        container = cli.create_container(image='nherbaut/simu-time',
                                         command="bash -c './bootstrap.sh > /dev/null && ./start.py -l DEBUG -i %lf -d %lf -t 3  >> /opt/simuservice/out/res.txt && echo hn:$HOSTNAME >> /opt/simuservice/out/res.txt && mkdir /opt/simuservice/out/$HOSTNAME && cp /opt/simuservice/*.svg /opt/simuservice/out/$HOSTNAME'" % (
                                             price, discount),
                                         host_config=cli.create_host_config(binds=[
                                             '/home/ubuntu/res:/opt/simuservice/out',

                                         ])

                                         )
        cli.start(container=container.get("Id"))
        print("new containers %s launched" % container.get("Id"))

