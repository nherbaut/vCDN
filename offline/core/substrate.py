#!/usr/bin/env python

import operator
from itertools import tee

import networkx as nx
import numpy.random
from haversine import haversine
from networkx.readwrite import json_graph
from pygraphml import GraphMLParser

from ..time.persistence import *

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')
DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')

substrate_to_node = Table('substrate_to_nodes', Base.metadata,
                          Column('node_id', Integer, ForeignKey('Node.id')),
                          Column('substrate_id', Integer, ForeignKey('Substrate.id'))
                          )

substrate_to_edge = Table('substrate_to_edges', Base.metadata,
                          Column('edge_id', Integer, ForeignKey('Edge.id')),
                          Column('substrate_id', Integer, ForeignKey('Substrate.id'))
                          )


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


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class Substrate(Base):
    __tablename__ = "Substrate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nodes = relationship("Node", secondary=substrate_to_node, cascade="all")
    edges = relationship("Edge", secondary=substrate_to_edge, cascade="all")

    def get_nxgraph(self):
        g = nx.Graph()
        for edge in self.edges:
            g.add_edge(edge.node_1.name, edge.node_2.name, attr_dict={"bandwidth": edge.bandwidth, "delay": edge.delay})
        return g

    def __str__(self):
        # print [x[1] for x in self.nodes.items()]
        return "%e\t%e" % (self.get_edges_sum(), self.get_edges_sum())

    def get_edges_sum(self):
        return sum([x.bandwidth for x in self.edges])

    def get_nodes_sum(self):
        return sum([x.cpu for x in self.nodes.items()])

    def get_nodes_by_bw(self):
        return self.__get_graph().degree(weight="bandwidth")

    def get_nodes_by_degree(self):
        return self.__get_graph().degree()

    def shortest_path(self, node1, node2):
        return nx.shortest_path(self.__get_graph(), node1, node2, weight="delay")

    def compute_delay(self, alist):
        return sum([self.__get_graph().get_edge_data(node1, node2)["delay"] for node1, node2 in pairwise(alist)])

    def __get_graph(self):
        if not hasattr(self, 'g'):
            self.g = nx.Graph()
            # it's silly to do that, as most of the underlying graph are nx.Graph objects...
            for node in self.nodes:
                self.g.add_node(node.name)

            for edge in self.edges:
                self.g.add_edge(edge.node_1.name, edge.node_2.name, bandwidth=edge.bandwidth, delay=edge.delay)

        return self.g

    def get_json(self):
        g = self.__get_graph()
        return json_graph.node_link_data(g)

    def __init__(self, edges, nodes):
        '''

        :param edges: a list of edge spec
        :param nodes: a dict of nodes spec
        :param cpuCost: the global cost for CPU
        :param netCost:  the global cost for network
        '''
        session = Session()
        self.edges = edges
        self.nodes = nodes
        self.edges_init = sorted(edges, key=lambda x: "%s%s" % (str(x.node_1), str(x.node_2)))

    def write(self, path="."):

        assert path != "."

        if not os.path.exists(os.path.join(RESULTS_FOLDER, path)):
            os.makedirs(os.path.join(RESULTS_FOLDER, path))

        edges_file = os.path.join(RESULTS_FOLDER, path, "substrate.edges.data")
        nodes_file = os.path.join(RESULTS_FOLDER, path, "substrate.nodes.data")
        edges = self.edges
        nodesdict = self.nodes
        with open(edges_file, 'w') as f:
            for edge in sorted(self.edges, key=lambda x: x.node_1.name):
                f.write("%s\n" % edge)

        with open(nodes_file, 'w') as f:
            for node in sorted(self.nodes, key=lambda x: x.name):
                f.write("%s\n" % node)

    @classmethod
    def __fromSpec(cls, args):
        width, height, bw, delay, cpu = args
        return cls.fromGrid(width=width, height=height, bw=bw, delay=delay, cpu=cpu)

    @classmethod
    def fromSpec(cls, specs, rs=numpy.random.RandomState()):
        if specs[0] == "jsonfile":
            return cls.__fromJson(list(specs[1]))
        elif specs[0] == "grid":
            return cls.__fromSpec(list(specs[1]))
        elif specs[0] == "links":
            return cls.fromLinks(list(specs[1]))
        elif specs[0] == "file":
            return cls.fromGraph(rs, specs[1])
        elif specs[0] == "powerlaw":
            return cls.fromPowerLaw(list(specs[1]))
        elif specs[0] == "erdos_renyi":
            return cls.FromErdosRenyi(list(specs[1]))
        else:
            raise ValueError("not a valid topology spec %s" % str(specs))

    @classmethod
    def __fromJson(cls, specs):
        json = specs

        json_graph

    @classmethod
    def fromLinks(cls, specs):
        name = specs[0]
        g = nx.Graph()
        # load all the links
        with open(os.path.join(DATA_FOLDER, "links", "operator-%s.links" % name)) as f:
            for line in f.read().split("\n"):
                nodes = line.strip().split(" ")
                while len(nodes) >= 2:
                    root = nodes.pop(0)
                    for node in nodes:
                        g.add_edge(root, node)

        # take the biggest connected subgraph
        g = max({sg: len(sg.nodes()) for sg in nx.connected_component_subgraphs(g)}.iteritems(),
                key=operator.itemgetter(1))[0]

        session = Session()
        nodes = [Node(name=str(n), cpu_capacity=100) for n in g.nodes()]
        nodesDict = {node.name: node for node in nodes}

        session.add_all(nodes)
        session.flush()

        Session.begin()
        edges = [Edge
                 (node_1=nodesDict[e[0]],
                  node_2=nodesDict[e[1]],
                  bandwidth=g.degree(e[0]) * g.degree(e[1]) * 10000000000,
                  delay=2
                  )
                 for e in g.edges()

                 ]

        session.add_all(edges)

        Session.commit()
        session.flush()

        return cls(edges, nodes)

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
        g = nx.powerlaw_cluster_graph(n, m, p, seed)
        session = Session()
        nodes = [Node(name=str(n), cpu_capacity=cpu) for n in g.nodes()]

        session.add_all(nodes)
        session.flush()

        edges = [Edge
                 (node_1=session.query(Node).filter(Node.name == str(e[0])).one(),
                  node_2=session.query(Node).filter(Node.name == str(e[1])).one(),
                  bandwidth=bw,
                  delay=delay
                  )
                 for e in g.edges()

                 ]
        session.add_all(edges)
        session.flush()

        return cls(edges, nodes
                   )

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
        g = nx.erdos_renyi_graph(n, p, seed)
        session = Session()
        nodes = [Node(name=str(n), cpu_capacity=cpu) for n in g.nodes()]

        session.add_all(nodes)
        session.flush()

        edges = [Edge
                 (node_1=session.query(Node).filter(Node.name == str(e[0])).one(),
                  node_2=session.query(Node).filter(Node.name == str(e[1])).one(),
                  bandwidth=bw,
                  delay=delay
                  )
                 for e in g.edges()

                 ]
        session.add_all(edges)
        session.flush()

        return cls(edges, nodes)

    @classmethod
    def fromGrid(cls, width=5, height=5, bw=10 ** 10, delay=10, cpu=10):
        width = int(width)
        height = int(height)
        session = Session()
        edges = []
        nodes = []

        for i in range(1, width + 1):
            for j in range(1, height + 1):
                node = Node(name=str("%02d%02d" % (i, j)), cpu_capacity=cpu)
                nodes.append(node)
                session.add(node)
                session.flush()

        for i in range(1, width + 1):
            for j in range(1, height + 1):

                if j + 1 <= height:
                    edge = Edge(node_1=session.query(Node).filter(Node.name == "%02d%02d" % (i, j)).one(),
                                node_2=session.query(Node).filter(Node.name == "%02d%02d" % (i, j + 1)).one(),
                                bandwidth=bw, delay=delay)
                    edges.append(edge)
                if i + 1 <= width:
                    edge = Edge(node_1=session.query(Node).filter(Node.name == "%02d%02d" % (i, j)).one(),
                                node_2=session.query(Node).filter(Node.name == "%02d%02d" % (i + 1, j)).one(),
                                bandwidth=bw, delay=delay)
                    edges.append(edge)
                if j + 1 <= height and i + 1 <= width:
                    edge = Edge(node_1=session.query(Node).filter(Node.name == "%02d%02d" % (i, j)).one(),
                                node_2=session.query(Node).filter(Node.name == "%02d%02d" % (i + 1, j + 1)).one(),
                                bandwidth=bw,
                                delay=delay)
                    edges.append(edge)

            for edge in edges:
                session.add(edge)
                session.flush()

        return cls(edges, nodes, )

    @classmethod
    def fromGraph(cls, rs, args):
        session = Session()
        file, cpu = args
        parser = GraphMLParser()

        g = parser.parse(os.path.join(DATA_FOLDER, file))
        nodes = [Node(name=str(n.id), cpu_capacity=cpu) for n in g.nodes()]
        nodes_from_g = {str(n.id): n for n in g.nodes()}
        session.add_all(nodes)
        session.flush()

        edges = [Edge
                 (node_1=session.query(Node).filter(Node.name == str(e.node1.id)).one(),
                  node_2=session.query(Node).filter(Node.name == str(e.node2.id)).one(),
                  bandwidth=float(e.attributes()["d42"].value),
                  delay=get_delay(nodes_from_g[str(e.node1.id)], nodes_from_g[str(e.node2.id)])
                  )

                 for e in g.edges() if
                 "d42" in e.attributes()
                 and isOK(nodes_from_g[str(e.node1.id)], nodes_from_g[str(e.node2.id)])
                 ]
        session.add_all(edges)
        session.flush()

        # filter out nodes for which we have edges
        valid_nodes = list(set([e.node_1.name for e in edges] + [e.node_2.name for e in edges]))
        nodes = list(set([n for n in nodes if str(n.name) in valid_nodes]))

        session.add_all(nodes)
        session.flush()
        session.add_all(edges)
        session.flush()

        return cls(edges, nodes)

    def release_service(self, service):
        self.__handle_service(service, +1)

    def consume_service(self, service):
        self.__handle_service(service, -1)

    def __handle_service(self, service, factor):
        session = Session()
        # print "consuming..."
        for ns in service.mapping.node_mappings:
            # get topo node
            ns.node.cpu_capacity = ns.node.cpu_capacity + factor * ns.service_node.cpu


            # print "\teater %lf flurom %s, remaining %s" % (service.nodes[ns[1]].cpu, ns[1], self)
        for es in service.mapping.edge_mappings:
            es.edge.bandwidth = es.edge.bandwidth + factor * es.serviceEdge.bandwidth

        session.flush()

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
