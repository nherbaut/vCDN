#!/usr/bin/env python

import functools
import operator
from itertools import tee

import networkx as nx
from haversine import haversine
from networkx.readwrite import json_graph
from pygraphml import GraphMLParser
from sqlalchemy.schema import Table

from offline.core.utils import weighted_shuffle
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
    return list(zip(a, b))


class Substrate(Base):
    __tablename__ = "Substrate"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nodes = relationship("Node", secondary=substrate_to_node, cascade="all")
    edges = relationship("Edge", secondary=substrate_to_edge, cascade="all")

    def get_closest_node(self, n1, targets, weight=None):
        '''

        :param n1: a node on the substrate
        :param targets: several other nodes on the substrate
        :param weight: optional weight the implement the "closest" logic
        :return: the one node amongst the targets to be the closests
        '''
        return \
            min([(target, nx.shortest_path_length(self.get_nxgraph(), n1, target, weight=weight)) for target in
                 targets],
                key=lambda x: x[1])[0]

    def get_nxgraph(self):
        g = nx.Graph()
        for node in self.nodes:
            g.add_node(node.name, attr_dict={"cpu": node.cpu_capacity})
        for edge in self.edges:
            g.add_edge(edge.node_1.name, edge.node_2.name, attr_dict={"bandwidth": edge.bandwidth, "delay": edge.delay})
        return g

    def __str__(self):
        # print [x[1] for x in self.nodes.items()]
        return "%e\t%e" % (self.get_edges_sum(), self.get_edges_sum())

    def get_edges_sum(self):
        return sum([x.bandwidth for x in self.edges])

    def get_nodes_sum(self):
        return sum([x.cpu for x in list(self.nodes.items())])

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

    @classmethod
    def __fromSpec(cls, args):
        width, height, bw, delay, cpu = args
        return cls.fromGrid(width=width, height=height, bw=bw, delay=delay, cpu=cpu)

    @classmethod
    def fromSpec(cls, specs, rs):
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
        elif specs[0] == "vcdn":
            return cls.from_vcdn(list(specs[1]))
        else:
            raise ValueError("not a valid topology spec %s" % str(specs))

    @classmethod
    def from_vcdn(cls, specs):

        graphs = []
        cdns = {}
        as_01 = nx.powerlaw_cluster_graph(30, 1, 0.2)
        as_01 = nx.relabel.relabel_nodes(as_01, {n: "AS01-%s" % n for n in as_01.nodes()})
        graphs.append(as_01)

        ipxes = list(weighted_shuffle(as_01, list(as_01.degree().values())))

        # cdn networks
        for i in range(1, 4):
            cdn_id = "CDN%02d" % i
            cdnas = nx.powerlaw_cluster_graph(3, 1, 1)
            cdnas = nx.relabel.relabel_nodes(cdnas, {n: "%s-%02d" % (cdn_id, n) for n in cdnas.nodes()})
            cdns[cdn_id] = cdnas
            graphs.append(cdnas)

        g = functools.reduce(lambda x, y: nx.compose(x, y), graphs)

        # transit/IPX
        for index, cdn in enumerate(cdns, 0):
            as_con = ipxes.pop()
            ipx = "TRIPX%02d-00" % index
            cdn_con = "%s-00" % cdn
            g.add_edge(as_con, ipx)
            g.add_edge(ipx, cdn_con)

        nodes = [Node(name=str(name), cpu_capacity=data.get("cpu", 99999)) for name, data in g.nodes(data=True)]

        session = Session()
        session.add_all(nodes)
        session.flush()

        edges = [Edge
                 (node_1=session.query(Node).filter(Node.name == str(n1)).one(),
                  node_2=session.query(Node).filter(Node.name == str(n2)).one(),
                  bandwidth=data.get("bw", 1000 * 1000 * 1000),
                  delay=data.get("delay", 1),
                  price_per_mbps=10 if "TRIPX02" in n2 or "TRIPX01" in n2 else 0
                  )
                 for n1, n2, data in g.edges(data=True)

                 ]
        session.add_all(edges)
        session.flush()

        return cls(edges, nodes
                   )

    @classmethod
    def from_service_graph(cls, service_graph):

        g = service_graph.nx_service_graph
        nodes = [Node(name=str(n[0]), cpu_capacity=n[1]["cpu"]) for n in g.nodes(data=True)]
        hops_delays_dict = service_graph.dump_delay_edge_dict()

        edges = [Edge
                 (node_1=next(node for node in nodes if node.name == str(node1)),
                  node_2=next(node for node in nodes if node.name == str(node2)),
                  bandwidth=data["bandwidth"],
                  delay=hops_delays_dict.get((str(node1), str(node2)), 0))
                 for node1, node2, data in g.edges(data=True)
                 ]

        session = Session()
        session.add_all(edges)
        session.add_all(nodes)
        session.flush()

        return cls(edges, nodes)

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
        g = max(list({sg: len(sg.nodes()) for sg in nx.connected_component_subgraphs(g)}.items()),
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

        g = nx.relabel.relabel_nodes(g, {n: "%s-%02d" % ("PL", n) for n in g.nodes()})

        nodes = [Node(name=str(n), cpu_capacity=cpu) for n in g.nodes()]

        session = Session()
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

        g = nx.relabel.relabel_nodes(g, {n: "%s-%02d" % ("ER", n) for n in g.nodes()})

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

        name_pattern = "GR-%02d%02d"

        for i in range(1, width + 1):
            for j in range(1, height + 1):
                node = Node(name=str(name_pattern % (i, j)), cpu_capacity=cpu)
                nodes.append(node)
                session.add(node)

        for i in range(1, width + 1):
            for j in range(1, height + 1):

                if j + 1 <= height:
                    edge = Edge(node_1=session.query(Node).filter(Node.name == name_pattern % (i, j)).one(),
                                node_2=session.query(Node).filter(Node.name == name_pattern % (i, j + 1)).one(),
                                bandwidth=bw, delay=delay)
                    edges.append(edge)
                if i + 1 <= width:
                    edge = Edge(node_1=session.query(Node).filter(Node.name == name_pattern % (i, j)).one(),
                                node_2=session.query(Node).filter(Node.name == name_pattern % (i + 1, j)).one(),
                                bandwidth=bw, delay=delay)
                    edges.append(edge)
                if j + 1 <= height and i + 1 <= width:
                    edge = Edge(node_1=session.query(Node).filter(Node.name == name_pattern % (i, j)).one(),
                                node_2=session.query(Node).filter(Node.name == name_pattern % (i + 1, j + 1)).one(),
                                bandwidth=bw,
                                delay=delay)
                    edges.append(edge)

            for edge in edges:
                session.add(edge)
        session.flush()

        return cls(edges, nodes, )

    @classmethod
    def fromGraph(cls, rs, args):

        file, cpu = args
        parser = GraphMLParser()

        gp = parser.parse(os.path.join(DATA_FOLDER, file))
        g = nx.Graph()
        nodes_from_g = {str(n.id): n for n in gp.nodes()}
        for nn in gp.nodes():
            if "d30" in nn.attributes():
                g.add_node(nn.id, cpu_capacity=cpu, name=nn.attributes()["d30"].value.replace(" ", "_"))

        for e in gp.edges():
            if "d42" in e.attributes() and isOK(nodes_from_g[str(e.node1.id)], nodes_from_g[str(e.node2.id)]):
                bandwidth = float(e.attributes()["d42"].value)
                delay = get_delay(nodes_from_g[str(e.node1.id)], nodes_from_g[str(e.node2.id)])
                node_1 = e.node1.id
                node_2 = e.node2.id
                g.add_edge(node_1, node_2, bandwidth=bandwidth, delay=delay)

        g = max(nx.connected_component_subgraphs(g), key=len)

        mapping = {k: "%s-%s" % ("GT", v["name"]) for k, v in g.nodes(data=True)}
        g = nx.relabel.relabel_nodes(g, mapping)

        session = Session()
        nodes = [Node(name=str(n), cpu_capacity=cpu) for n in g.nodes()]

        session.add_all(nodes)
        session.flush()

        nodes_by_name = {node.name: node for node in nodes}

        edges = [Edge
                 (node_1_id=nodes_by_name[str(e[0])].id,
                  node_2_id=nodes_by_name[str(e[1])].id,
                  bandwidth=e[2]["bandwidth"],
                  delay=e[2]["delay"]
                  )
                 for e in g.edges(data=True)

                 ]
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
        candidate_edges = [x for x in edges if x[0] == es.start_topo_node_id and x[1] == es.end_topo_node_id]
        if len(candidate_edges) != 0:
            sub_edge = candidate_edges[0]
            service_edge = service.spec.edges["%s %s" % (es.start_service_node_id, es.end_service_node_id)]
            edges.remove(sub_edge)
            edges.append((sub_edge[0], sub_edge[1], sub_edge[2] - service_edge.bw, sub_edge[3]))
            if sub_edge[2] - service_edge.bw < 0:
                print()
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
