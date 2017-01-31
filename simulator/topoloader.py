from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import Docker
from mininet.topo import Topo
import math
import numpy as np
import re


rs = np.random.RandomState()


class TopoDB(Topo):

    def __init__(self):
        pass

class loadTopo(Topo):
    "Simple topology example."

    def __init__(self, edges_file, nodes_file, CDNfile, startersfile, solutionsfile,service_edges):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        # Add hosts and switches
        self._hosts = {}
        self._switches = {}
        self._link = {}
        self._cmd = {}

        edges = []
        nodesdict = {}

        cdn_candidates = []
        starters_candiates = []
        nodesSol = []
        edgesSol = []
        bwSol=[]

        with open(nodes_file, 'r') as f:
            for line in f.read().split("\n"):
                if len(line) > 2:
                    nodeid, cpu = line.split("\t")
                    nodesdict[nodeid] = float(cpu)

                    self._switches["s%s" % (nodeid)] = self.addSwitch("s%s" % (nodeid), dpid="%s" % (nodeid))


        with open(service_edges, 'r') as f:
            for line in f.read().split("\n"):
                if len(line) > 2:
                    node1,node2, bw = line.split(" ")
                    bwSol.append(line.split(" "));


        with open(edges_file, 'r') as f:
            for line in f.read().split("\n"):
                if len(line) > 2:
                    node1, node2, bw, delay = line.split("\t")
                    edges.append((node1, node2, float(bw), float(delay)))
                    self._link["s%s-s%s" % (node1, node2)] = self.addLink(self._switches["s%s" % (node1)],
                                                                          self._switches["s%s" % (node2)],
                                                                          port1=int(node2),
                                                                          port2=int(node1),
                                                                          bw=float(bw) / 1000000 / 1000,
                                                                          delay='%sms' % (float(delay)),
                                                                          key="s%s-s%s" % (node1, node2))

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
        i = 0;
        for node in nodesSol:
            if node[1] != "S0":
                i += 1;
                name = node[1]
                ip = '10.0.0.%i' % i
                mac = '00:00:00:00:00:%i' % i
                if "VHG" in node[1]:
                    self._hosts[node[1]] = self.addHost(node[1], cls=Docker, dimage="ubuntu:trusty", ip=ip, mac=mac)
                    self._link["s%s-s%s" % (node1, node2)] = self.addLink(node[1], "s%s" % node[0],
                                                                          port2=20000 + int(
                                                                              "%s" % re.findall('\d+', node[1])[0]))
                elif "TE" in node[1]:
                    self._hosts[node[1]] = self.addHost(node[1], cls=Docker, dimage="ubuntu:trusty")

                    for nodealt in nodesSol:
                        if nodealt[1] != "S0":
                            if "S" in nodealt[1]:
                                # ialt += 1;
                                ipalt = '10.0.%s.%i/8' % (re.findall('\d+', nodealt[1])[0], i)
                                macalt = '00:00:00:00:%s:%i' % (re.findall('\d+', nodealt[1])[0], i)
                                bwsol=0;
                                for node1alt,node2alt,bw in bwSol:
                                    if ((node1alt==nodealt[1]) and ("VHG" in node2alt )):
                                        bwsol=bw

                                self._link["s%s-s%s-%s" % (node1, node2, re.findall('\d+', nodealt[1])[0])] = \
                                    self.addLink(node[1], "s%s" % node[0],
                                                 port2=30000 + int("%s" % re.findall('\d+', node[1])[0]) + int(
                                                     "%s" % re.findall('\d+', nodealt[1])[0]) * 100,
                                                 params1={"ip": ipalt, "mac": macalt},
                                                 intfName1='eth%s' % re.findall('\d+', nodealt[1])[0],
                                                 bw=float(bwsol) / 1000000 / 1000 )
                                if not node[1] in self._cmd:
                                    self._cmd[node[1]] = []

                                self._cmd[node[1]].append(
                                    'ip addr add %s dev %s' % (ipalt, 'eth%s' % re.findall('\d+', nodealt[1])[0]))



                elif "S" in node[1]:
                    self._hosts[node[1]] = self.addHost(node[1], cls=Docker, dimage="ubuntu:trusty", ip=ip, mac=mac)
                    self._link["s%s-s%s" % (node1, node2)] = self.addLink(node[1], "s%s" % node[0],
                                                                          port2=10000 + int(
                                                                              "%s" % re.findall('\d+', node[1])[0]))
                elif "CDN" in node[1]:
                    self._hosts[node[1]] = self.addHost(node[1], cls=Docker, dimage="ubuntu:trusty", ip=ip, mac=mac)
                    self._link["s%s-s%s" % (node1, node2)] = self.addLink(node[1], "s%s" % node[0],
                                                                          port2=40000 + int(
                                                                              "%s" % re.findall('\d+', node[1])[0]))
                else:
                    print('error')

        pass


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
