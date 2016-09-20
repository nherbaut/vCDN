#!/usr/bin/env python

import argparse
import os
from functools import partial

import numpy as np
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.net import Containernet
from mininet.node import RemoteController, OVSSwitch

from simulator.topoloader import loadTopo

rs = np.random.RandomState()
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'offline/results')

parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument('--pickle', help="solution file pickle", default="mapping.data", type=str)
args = parser.parse_args()


# with open("mapping.data", 'r') as f:
#     data = pickle.load(f)
# print "ok"
# with open("service.pickle", "r") as f:
#     service = pickle.load(f)






def topology():
    "Create a network with some docker containers acting as hosts."
    edgefile = os.path.join(RESULTS_FOLDER, "./substrate.edges.empty.data")
    nodesfile = os.path.join(RESULTS_FOLDER, "./substrate.nodes.data")
    CDNfile = os.path.join(RESULTS_FOLDER, "CDN.nodes.data")
    startersFile = os.path.join(RESULTS_FOLDER, "starters.nodes.data")
    solutionsFile = os.path.join(RESULTS_FOLDER, "solutions.data")
    service_edges = os.path.join(RESULTS_FOLDER, "./service.edges.data")
    switch = partial( OVSSwitch, protocols='OpenFlow13')

    topo = loadTopo(edgefile, nodesfile, CDNfile, startersFile, solutionsFile,service_edges)

    c = RemoteController('c', '0.0.0.0', 6633)
    # topodock=  loaddocker(os.path.join(RESULTS_FOLDER, "./substrate.edges.data"), os.path.join(RESULTS_FOLDER, "./substrate.nodes.data"))
    info('*** Start Containernet\n')
    net = Containernet(topo=topo, controller=c, link=TCLink,switch=switch)
    for host in net.hosts:
        if host.name in topo._cmd:
            for cmd in topo._cmd[host.name]:
                print "send cmd"
                print (host.sendCmd(cmd))



    info('*** Starting network\n')
    net.start()

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
