#! /usr/bin/env python

import argparse
from docker import Client
import numpy
import time


parser = argparse.ArgumentParser()
parser.add_argument('container_id', metavar='ID', type=str)
args = parser.parse_args()
cli = Client(base_url='unix://var/run/docker.sock')
for container in cli.containers(filters={"status":"exited","since":args.container_id}):
  print("%s,%s"%(container.get("Id")[0:15],cli.logs(container=container.get("Id")).split("\n")[-2]))
