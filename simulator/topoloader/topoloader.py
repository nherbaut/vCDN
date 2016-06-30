from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import Docker
from mininet.topo import Topo
import math
import numpy as np
import re
rs = np.random.RandomState()

class loadTopo(Topo):
    "Simple topology example."

    def __init__(self, edges_file, nodes_file, CDNfile, startersfile, solutionsfile):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        # Add hosts and switches
        self._hosts = {}
        self._switches = {}
        self._link = {}

        edges = []
        nodesdict = {}

        cdn_candidates = []
        starters_candiates = []
        nodesSol = []
        edgesSol = []

        with open(nodes_file, 'r') as f:
            for line in f.read().split("\n"):
                if len(line) > 2:
                    nodeid, cpu = line.split("\t")
                    nodesdict[nodeid] = float(cpu)
                    self._switches["s%s" % (nodeid)] = self.addSwitch("s%s" % (nodeid))

        with open(edges_file, 'r') as f:
            for line in f.read().split("\n"):
                if len(line) > 2:
                    node1, node2, bw, delay = line.split("\t")
                    edges.append((node1, node2, float(bw), float(delay)))
                    self.addLink(self._switches["s%s" % (node1)], self._switches["s%s" % (node2)],
                                 bw=float(bw)/1000000000, delay='%sms'% (float(delay)), key="s%s-s%s" % (node1, node2))


        # size=4
        # docker = [self.addDocker("d%d"%i, ip='192.168.80.%d'%i,dcmd= '-s', dimage="networkstatic/iperf3") for i in range(1,size+1) ]
        # docker = [self.addHost("d%d"%i) for i in range(1,size+1) ]
        # docker = [self.addHost("d%d"%i, cls=Docker, dcmd= '-s',dimage="networkstatic/iperf3") for i in range(1,size+1) ]
        # docker = [self.addHost("d%d"%i, cls=Docker, dimage="ubuntu:trusty") for i in range(1,size+1) ]


        # for i in range(0,size):
        #     self.addLink(docker[i], np.random.choice(self._switches.keys()))




        # with open(CDNfile, 'r') as f:
        #     data = f.read()
        #     j=0;
        #     for line in data.split("\n"):
        #         line = line.split("\t")
        #         if len(line) == 2:
        #             cdn_candidates.append(line[1])
        #             self.addHost("cdn%d"%j, cls=Docker, dcmd= '-s',dimage="networkstatic/iperf3")
        #             self.addLink("cdn%d"%j,"s%s"%line[1])
        #             j+=1
        #
        #
        # with open(startersfile, 'r') as f:
        #     data = f.read()
        #     for line in data.split("\n"):
        #         line = line.split("\t")
        #         if len(line) == 2:
        #             starters_candiates.append(line[1])
        #             self.addHost("start%d"%j, cls=Docker, dcmd= '-s',dimage="networkstatic/iperf3")
        #             self.addLink("start%d"%j,"s%s"%line[1])
        #             j+=1


        with open(solutionsfile, "r") as sol:
            data = sol.read().split("\n")

            for line in data:
                matches = re.findall("^x\$(.*)\$([^ \t]+)", line)
                if (len(matches) > 0):
                    nodesSol.append(matches[0])
                    continue
                matches = re.findall("^y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
                if (len(matches) > 0):
                    edgesSol.append(matches[0])
                    continue

        for node in nodesSol:
            if node[1] != "S0":
                name=node[1]
                if "VHG" in node[1]:

                    self.addHost(node[1], cls=Docker, dcmd= '-s',dimage="networkstatic/iperf3")
                    self.addLink(node[1],"s%s"%node[0])

                elif "vCDN" in node[1]:
                    self.addHost(node[1], cls=Docker, dcmd= '-s',dimage="networkstatic/iperf3")
                    self.addLink(node[1],"s%s"%node[0])
                elif "S" in node[1]:
                    self.addHost(node[1], cls=Docker, dcmd= '-s',dimage="networkstatic/iperf3")
                    self.addLink(node[1],"s%s"%node[0])
                elif "CDN" in node[1]:
                    self.addHost(node[1], cls=Docker, dcmd= '-s',dimage="networkstatic/iperf3")
                    self.addLink(node[1],"s%s"%node[0])
                else :
                    print 'error'



























        # self._switches["s11"] = self.addSw            itch("s11")
        # self._switches["s12"] = self.addSw            itch("s12")
        # self._switches["s21"] = self.addSw            itch("s21")
        # self._switches["s31"] = self.addSw            itch("s31")
        # self._switches["s32"] = self.addSwitc            h("s32")



        #
        # self.addLink(self._switches["s11"], self._switches["s21"], bw=1000, delay='5ms',key="%s-%s" % ("s1            1", "s21"))
        # self.addLink(self._switches["s12"], self._switches["s21"], bw=1000, delay='5ms',key="%s-%s" % ("s1            2", "s21"))
        # self.addLink(self._switches["s21"], self._switches["s31"], bw=1000, delay='5ms',key="%s-%s" % ("s2            1", "s31"))
        # self.addLink(self._switches["s21"], self._switches["s32"], bw=1000, delay='5ms',key="%s-%s" % ("s21", "s32"))
#
# class loaddocker(Mininet):
#      def __init__(self, edges_file, nodes_file):
#
#         "Create custom topo."
#         Mininet.__init__(self)
#
#         topo= loadTopo(edges_file, nodes_file)
#         size=4
#         #docker = [self.addDocker("d%d"%i, ip='192.168.80.%d'%i,dcmd= '-s', dimage="networkstatic/iperf3") for i in range(1,size+1) ]
#         docker = [self.addHost("d%d"%i, cls=Docker) for i in range(1,size+1) ]
#
#
#         for i in range(0,size):
#             self.addLink(docker[i], np.random.choice(topo._switches.keys()))
#






topos = {'mytopo': (lambda: loadTopo("./substrate.edges.data", "./substrate.nodes.data"))}
