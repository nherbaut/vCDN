#!/usr/bin/env python

import networkx
import numpy.random
from haversine import haversine
from pygraphml import GraphMLParser

from ..time.persistence import *

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')
DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')

substrate_to_node = Table('substrate_to_nodes', Base.metadata,
                          Column('node_id', String(16), ForeignKey('Node.id')),
                          Column('substrate_id', Integer, ForeignKey('Substrate.id'))
                          )

substrate_to_edge = Table('substrate_to_edges', Base.metadata,
                          Column('edge_id', Integer, ForeignKey('Edge.id')),
                          Column('substrate_id', Integer, ForeignKey('Substrate.id'))
                          )


class Substrate(Base):
    __tablename__ = "Substrate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nodes = relationship("Node", secondary=substrate_to_node, cascade="all")
    edges = relationship("Edge", secondary=substrate_to_edge, cascade="all")

    def __str__(self):
        # print [x[1] for x in self.nodes.items()]
        return "%e\t%e" % (self.get_edges_sum(), self.get_edges_sum())

    def get_edges_sum(self):
        return sum([x.bandwidth for x in self.edges])

    def get_nodes_sum(self):
        return sum([x.cpu for x in self.nodes.items()])

    def __init__(self, edges, nodesdict):
        '''

        :param edges: a list of edge spec
        :param nodesdict: a dict of nodes spec
        :param cpuCost: the global cost for CPU
        :param netCost:  the global cost for network
        '''
        self.edges = edges
        self.nodes = nodesdict
        self.edges_init = sorted(edges, key=lambda x: "%s%s" % (str(x.node_1), str(x.node_2)))

    def write(self, path="."):

        if not os.path.exists(os.path.join(RESULTS_FOLDER, path)):
            os.makedirs(os.path.join(RESULTS_FOLDER, path))

        edges_file = os.path.join(RESULTS_FOLDER, path, "substrate.edges.data")
        nodes_file = os.path.join(RESULTS_FOLDER, path, "substrate.nodes.data")
        edges = self.edges
        nodesdict = self.nodes
        with open(edges_file, 'w') as f:
            for edge in self.edges:
                f.write("%s\n" % edge)

        with open(nodes_file, 'w') as f:
            for node in self.nodes:
                f.write("%s\n" % node)

    @classmethod
    def __fromSpec(cls, args):
        width, height, bw, delay, cpu = args
        return cls.fromGrid(width=width, height=height, bw=bw, delay=delay, cpu=cpu)

    @classmethod
    def fromSpec(cls, specs, rs=numpy.random.RandomState()):
        if specs[0] == "grid":
            return cls.__fromSpec(list(specs[1]) + [10 ** 10, 1, 5])
        elif specs[0] == "file":
            return cls.fromGraph(rs, specs[1][0])
        elif specs[0] == "powerlaw":
            return cls.fromPowerLaw(list(specs[1]) + [10 ** 10, 1, 5])
        elif specs[0] == "erdos_renyi":
            return cls.FromErdosRenyi(list(specs[1]) + [10 ** 10, 1, 5])
        else:
            return cls.__fromSpec([5, 5] + [10 ** 10, 1, 5])

    @classmethod
    def fromPowerLaw(cls, specs):
        '''
        :param specs: a tupple containing (n, m, p, seed, bw, delay, cpu)
        :return: a substrate
        '''
        n, m, p, seed, bw, delay, cpu = specs
        n = int(n)
        m = int(m)
        p = float(p)
        seed = int(seed)
        edges = []
        nodesdict = {}
        g = networkx.powerlaw_cluster_graph(n, m, p, seed)
        for node in g.nodes():
            nodesdict[str(node + 1)] = cpu

        for i, j in g.edges():
            edges.append((str(i + 1), str(j + 1), bw, delay))

        return cls(edges, nodesdict)

    @classmethod
    def FromErdosRenyi(cls, specs):
        '''
        :param specs: a tuple containing n, p, seed, bw, delay, cpu
        :return: the substrate
        '''
        n, p, seed, bw, delay, cpu = specs
        n = int(n)
        p = float(p)
        seed = int(seed)
        edges = []
        nodesdict = {}
        g = networkx.erdos_renyi_graph(n, p, seed)
        for node in g.nodes():
            nodesdict[str(node + 1)] = cpu

        for i, j in g.edges():
            edges.append((str(i + 1), str(j + 1), bw, delay))

        return cls(edges, nodesdict)

    @classmethod
    def fromGrid(cls, width=5, height=5, bw=10 ** 10, delay=10, cpu=10):
        session=Session()
        edges = []
        nodes = []

        for i in range(1, width + 1):
            for j in range(1, height + 1):
                node = Node(id=str("%02d%02d" % (i, j)), cpu_capacity=cpu)
                nodes.append(node)
                session.add(node)
                session.flush()

        for i in range(1, width + 1):
            for j in range(1, height + 1):
                if j + 1 <= height:
                    edge = Edge(node_1="%02d%02d" % (i, j), node_2="%02d%02d" % (i, j + 1), bandwidth=bw, delay=delay)
                    edges.append(edge)
                if i + 1 <= width:
                    edge = Edge(node_1="%02d%02d" % (i, j), node_2="%02d%02d" % (i + 1, j), bandwidth=bw, delay=delay)
                    edges.append(edge)
                if j + 1 <= height and i + 1 <= width:
                    edge = Edge(node_1="%02d%02d" % (i, j), node_2="%02d%02d" % (i + 1, j + 1), bandwidth=bw,
                                delay=delay)
                    edges.append(edge)

            for edge in edges:
                session.add(edge)
                session.flush()

        return cls(edges, nodes, )

    @classmethod
    def fromFile(cls, edges_file=os.path.join(RESULTS_FOLDER, "substrate.edges.data"),
                 nodes_file=os.path.join(RESULTS_FOLDER, "substrate.nodes.data")):

        edges = []
        nodesdict = {}

        with open(edges_file, 'r') as f:
            for line in f.read().split("\n"):
                if len(line) > 2:
                    node1, node2, bw, delay = line.split("\t")
                    edges.append((node1, node2, float(bw), float(delay)))

        with open(nodes_file, 'r') as f:
            for line in f.read().split("\n"):
                if len(line) > 2:
                    nodeid, cpu = line.split("\t")
                    nodesdict[nodeid] = float(cpu)

        return cls(edges, nodesdict)

    @classmethod
    def fromGraph(cls, rs, file):
        parser = GraphMLParser()

        g = parser.parse(os.path.join(DATA_FOLDER, file))

        nodes = {str(n.id): n for n in g.nodes()}
        edges = [(str(e.node1.id), str(e.node2.id), float(e.attributes()["d42"].value),
                  get_delay(nodes[str(e.node1.id)], nodes[str(e.node2.id)]))
                 for e in g.edges() if "d42" in e.attributes() and isOK(nodes[str(e.node1.id)], nodes[str(e.node2.id)])]

        # for which we have all the data
        valid_nodes = list(set([e[0] for e in edges] + [e[1] for e in edges]))

        nodes = set([str(n.id) for n in g.nodes() if str(n.id) in valid_nodes])
        nodesdict = {}

        for l in nodes:
            value = max(rs.normal(100, 5, 1)[0], 0)
            nodesdict[str(l)] = value

        return cls(edges, nodesdict)

    def release_service(self, service):
        self.__handle_service(service, +1)

    def consume_service(self, service):
        self.__handle_service(service, -1)

    def __handle_service(self, service, factor):

        # print "consuming..."
        for ns in service.mapping.node_mappings:
            # get topo node
            ns.node.cpu_capacity = ns.node.cpu_capacity + factor * ns.service_node.cpu

            # print "\teater %lf flurom %s, remaining %s" % (service.nodes[ns[1]].cpu, ns[1], self)
        for es in service.mapping.edge_mappings:
            es.edge.bandwidth = es.edge.bandwidth + factor * es.serviceEdge.bandwidth

    def deduce_bw(es, edges, service):
        candidate_edges = filter(lambda x: x[0] == es.start_topo_node_id and x[1] == es.end_topo_node_id, edges)
        if len(candidate_edges) != 0:
            sub_edge = candidate_edges[0]
            service_edge = service.spec.edges["%s %s" % (es.start_service_node_id, es.end_service_node_id)]
            edges.remove(sub_edge)
            edges.append((sub_edge[0], sub_edge[1], sub_edge[2] - service_edge.bw, sub_edge[3]))
            if sub_edge[2] - service_edge.bw < 0:
                print
                "hein?"
            return True
        return False

    def get_delay(node1, node2):
        return haversine((float(node1.attributes()["d29"].value), float(node1.attributes()["d32"].value)),
                         (float(node2.attributes()["d29"].value), float(node2.attributes()["d32"].value))) / (
                   299.300 * 0.6)

    def isOK(node1, node2):
        try:
            get_delay(node1, node2)
        except:
            return False
        return True

    def get_substrate(rs, file=os.path.join(DATA_FOLDER, 'Geant2012.graphml')):
        su = Substrate.fromGraph(rs, file)
        su.write()

        return su

    class bcolors:
        @staticmethod
        def color_out(value):
            HEADER = '\033[95m'
            OKBLUE = '\033[94m'
            OKGREEN = '\033[92m'
            WARNING = '\033[93m'
            FAIL = '\033[91m'
            ENDC = '\033[0m'
            BOLD = '\033[1m'
            UNDERLINE = '\033[4m'
            if value > 80:
                return OKGREEN + str(value) + ENDC
            elif value > 60:
                return OKBLUE + str(value) + ENDC
            elif value > 40:
                return WARNING + str(value) + ENDC
            elif value > 20:
                return FAIL + str(value) + ENDC
            else:
                return FAIL + BOLD + str(value) + ENDC
