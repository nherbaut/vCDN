"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo


class MyTopo(Topo):
    "Simple topology example."

    def __init__(self):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        # Add hosts and switches
        self._hosts = {}
        self._switches = {}
        self._link = {}

        self._switches["s11"] = self.addSwitch("s11")
        self._switches["s12"] = self.addSwitch("s12")
        self._switches["s21"] = self.addSwitch("s21")
        self._switches["s31"] = self.addSwitch("s31")
        self._switches["s32"] = self.addSwitch("s32")

        self._hosts["h11"] = self.addHost("h11")
        self._hosts["h12"] = self.addHost("h12")
        self._hosts["h21"] = self.addHost("h21")
        self._hosts["h31"] = self.addHost("h31")
        self._hosts["h32"] = self.addHost("h32")

        self.addLink(self._hosts["h11"], self._switches["s11"], bw=1000, delay='5ms',key="%s-%s" % ("h11", "s11"))
        self.addLink(self._hosts["h12"], self._switches["s12"], bw=1000, delay='5ms',key="%s-%s" % ("h12", "s12"))
        self.addLink(self._hosts["h21"], self._switches["s21"], bw=1000, delay='5ms',key="%s-%s" % ("h21", "s21"))
        self.addLink(self._hosts["h31"], self._switches["s31"], bw=1000, delay='60ms',key="%s-%s" % ("h31", "s31"))
        self.addLink(self._hosts["h32"], self._switches["s32"], bw=50, delay='30ms',key="%s-%s" % ("h32", "s32"))


        self.addLink(self._switches["s11"], self._switches["s21"], bw=1000, delay='5ms',key="%s-%s" % ("s11", "s21"))
        self.addLink(self._switches["s12"], self._switches["s21"], bw=1000, delay='5ms',key="%s-%s" % ("s12", "s21"))
        self.addLink(self._switches["s21"], self._switches["s31"], bw=1000, delay='5ms',key="%s-%s" % ("s21", "s31"))
        self.addLink(self._switches["s21"], self._switches["s32"], bw=1000, delay='5ms',key="%s-%s" % ("s21", "s32"))



topos = {'mytopo': (lambda: MyTopo())}
