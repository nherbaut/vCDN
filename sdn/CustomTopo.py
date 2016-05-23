"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo
from mininet.node import OVSSwitch


class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        self._hosts={}
        self._switches={}

        sizex=5
        sizey=1

        for i in range(0,sizex):
            for j in range (0,sizey):
                names="s%d%d"%(i,j)
                self._switches[names]=self.addSwitch(names)
                nameh="h%d%d"%(i,j)
                self._hosts[nameh]=self.addHost(nameh)
                self.addLink(self._hosts[nameh], self._switches[names], bw=1000, delay='5ms')


        for i in range(0,sizex):
            for j in range (0,sizey):
                if j+1 < sizey:
                    self.addLink(self._switches["s%d%d" % (i, j)], self._switches["s%d%d" % (i, j + 1)])
                if i+1 < sizex:
                    self.addLink(self._switches["s%d%d" % (i, j)], self._switches["s%d%d" % (i + 1, j)])



topos = { 'mytopo': ( lambda: MyTopo() ) }
