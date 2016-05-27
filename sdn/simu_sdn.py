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
h31.cmd('http-server -p 8000 -a %s . > h31.log &' % h31.IP())
h32.cmd('http-server -p 8000 -a %s . > h32.log &' % h32.IP())
h21.cmd('./proxy/startproxy.sh > proxy.log &')

h11.cmd('./dash_pool.py --mini_buffer_seconds 5 --maxi_buffer_seconds 10 --name h11 --host %s --port 8000 --path data --user_count=200 --arrival_time=0.5 --target_br=200000 --movie_size 20000000 --proxy_host %s --proxy_port 8082 > dash_pool.log&'%(h32.IP(),h21.IP()))
#h12.cmd('./dash_pool.py  --name h11 --host %s --port 8000 --path data --user_count=1000 --arrival_time=0.5 --target_br=500000 --movie_size 100000000 --proxy_host %s --proxy_port 8082&'%(h32.IP(),h21.IP()))
#h11.cmd('./dash_pool.py  --name h12 --host %s --port 8000 --path data --user_count=1000 --arrival_time=1 --target_br=2000000&'%h32.IP())
#print res
#CLI(net)
print "press enter to stop mininet"
sys.stdin.readline()
print "stopping mininet"
net.stop()
print "mininet is stopped"
