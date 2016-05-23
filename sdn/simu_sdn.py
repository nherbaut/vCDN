#!/usr/bin/env python


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import RemoteController

from CustomTopo import MyTopo
from mininet.node import OVSSwitch
from functools import partial



from functools import reduce
c = RemoteController('c', '0.0.0.0', 6633)
switch = partial( OVSSwitch, protocols='OpenFlow13' )
net = Mininet(topo=MyTopo(), link=TCLink,controller=c,switch=switch)
net.start()


h00 , h10, h20, h30 = net.get('h00', "h10", "h20", "h30")

net.pingAll()
h20.cmd('python -m SimpleHTTPServer > h20.logs &')
h30.cmd('python -m SimpleHTTPServer > h30.logs &')

res=h10.cmd('/home/nherbaut/workspace/algotel2016-code/sdn/dash_pool.py --host=%s --path="data" --port="8000" '%h20.IP())
print res






net.stop()
