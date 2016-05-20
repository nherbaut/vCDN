"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        hosts={}
        switches={}

        sizex=5
        sizey=2

        for i in range(0,sizex):
            for j in range (0,sizey):
                names="s%d%d"%(i,j)
                switches[names]=self.addSwitch( names )
                nameh="h%d%d"%(i,j)
                hosts[nameh]=self.addHost( nameh )
                self.addLink( hosts[nameh], switches[names] )


        for i in range(0,sizex):
            for j in range (0,sizey):
                if j+1 < sizey:
                    self.addLink( switches["s%d%d"%(i,j)], switches["s%d%d"%(i,j+1)] )
                if i+1 < sizex:
                    self.addLink( switches["s%d%d"%(i,j)], switches["s%d%d"%(i+1,j)] )



topos = { 'mytopo': ( lambda: MyTopo() ) }
