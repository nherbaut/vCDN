#!/usr/bin/env python


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import RemoteController, Controller, OVSController

from CustomTopo import MyTopo
from mininet.node import OVSSwitch
from functools import partial
from mininet.cli import CLI
import sys


from functools import reduce



c = RemoteController('c', '0.0.0.0', 6633)
#c= OVSController("c0")
switch = partial( OVSSwitch, protocols='OpenFlow13')
topo=MyTopo()
net = Mininet(topo=topo, link=TCLink,controller=c,switch=switch)


net.start()
net.pingAll(timeout=1)
h11, h12, h21, h31,h32= net.get('h11', "h12", "h21", "h31","h32")
cli=CLI(net)
cli.do_xterm(h11)
#h11.MAC()
h31.cmd('python -m SimpleHTTPServer > h20.logs &')
h32.cmd('python -m SimpleHTTPServer > h30.logs &')
res=h11.cmd('/home/nherbaut/workspace/algotel2016-code/sdn/dash_pool.py --host=%s --path="data" --port="8000" &'%h32.IP())
#print res
print "press enter to stop mininet"
sys.stdin.readline()
print "stopping mininet"
net.stop()
print "mininet is stopped"
