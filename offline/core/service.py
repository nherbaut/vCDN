import sys

import networkx as nx
from networkx.algorithms.components.connected import node_connected_component
from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from ..core.combinatorial import get_node_clusters
from ..core.solver import solve
from ..time.persistence import *

OPTIM_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../optim')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


class Node:
    def __init__(self, cpu):
        self.cpu = cpu


class Edge:
    def __init__(self, bw):
        self.bw = bw


class ServiceSpecFactory:
    @classmethod
    def instance(cls, sla, su, vmg_count, vcdn_count):
        return ServiceSpec(sla.get_start_nodes(), sla.get_cdn_nodes(), su)


class ServiceSpec:
    def __init__(self, su, cdn_ratio=0.35, cpu_vmg=1, cpu_vcdn=5, start_nodes=[], cdn_nodes=[], vmg_count=0,
                 vcdn_count=0):
        self.cdn_ratio = cdn_ratio
        self.cpu_vmg = cpu_vmg
        self.cpu_vcdn = cpu_vcdn
        self.start_nodes = start_nodes
        self.cdn_nodes = cdn_nodes
        self.su = su
        self.vmg_count = vmg_count
        self.vcdn_count = vcdn_count

    def get_vmg_id(self, start_node_id):
        return 0

    def get_vcdn_id(self, vhg_id):
        return 0


class ServiceTopo:
    def __init__(self, sla, vhg_count, vcdn_count):
        self.sla = sla
        self.servicetopo = self.__compute_service_topo(sla, vhg_count, vcdn_count)

    def __compute_service_topo(self, sla, vhg_count, vcdn_count):
        service = nx.Graph(sla=sla)
        service.add_node("S0", cpu=0)

        for i in range(1, vhg_count + 1):
            service.add_node("VHG%d" % i, type="VHG", cpu=1)

        for i in range(1, vcdn_count + 1):
            service.add_node("vCDN%d" % i, type="VCDN", cpu=5)

        for index, cdn in enumerate(sla.get_cdn_nodes(), start=1):
            service.add_node("CDN%d" % index, type="CDN", cpu=0)

        for key, topoNode in enumerate(sla.get_start_nodes(), start=1):
            service.add_node("S%d" % key, cpu=0, type="S", mapping=topoNode.toponode_id)
            service.add_edge("S0", "S%d" % key, delay=sys.maxint, bandwidth=10)

        for toponode_id, vmg_id in get_node_clusters(map(lambda x: x.toponode_id, sla.get_start_nodes()), vhg_count,
                                                     substrate=sla.substrate).items():
            service.add_edge("VHG%d" % vmg_id, "S%d" % vmg_id, delay=sys.maxint, bandwidth=0)

        return service

    def dump_nodes(self):
        '''
        :return: a list of tuples containing nodes and their properties
        '''
        res = []
        for node in node_connected_component(self.servicetopo, "S0"):
            res.append((node+"_%d"%self.sla.id, self.servicetopo.node[node]["cpu"]))
        return res

    def dump_edges(self):
        '''
        :return: a list of tuples containing nodes and their properties
        '''
        res = []
        for start, ends in self.servicetopo.edge.items():
            for end in ends:
                edge = self.servicetopo[start][end]
                res.append((start+"_%d"%self.sla.id, end+"_%d"%self.sla.id, edge["delay"], edge["bandwidth"]))
        return res


def get_count_by_type(self, type):
    return filter(lambda x: x[2]["type"] == 'x', self.servicetopo.edges_iter(data=True))


def get_vhg_count(self):
    return len(self.get_count_by_type("VHG"))


def get_vcdn_count(self):
    return len(self.get_count_by_type("VCDN"))


class Service(Base):
    __tablename__ = "Service"
    id = Column(Integer, primary_key=True, autoincrement=True)
    serviceNodes = relationship("ServiceNode", cascade="all")
    serviceEdges = relationship("ServiceEdge", cascade="all")
    slas = relationship("Sla", secondary=service_to_sla, back_populates="services")
    mapping = relationship("Mapping", cascade="all")

    @classmethod
    def cleanup(cls):
        for f in [os.path.join(RESULTS_FOLDER, "service.edges.data"),
                  os.path.join(RESULTS_FOLDER, "service.path.data"),
                  os.path.join(RESULTS_FOLDER, "service.path.delay.data"),
                  os.path.join(RESULTS_FOLDER, "service.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "CDN.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "starters.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "cdnmax.data"),
                  os.path.join(RESULTS_FOLDER, "VHG.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "VCDN.nodes.data")]:
            if os.path.isfile(f):
                os.remove(f)

    def get_service_specs(self, include_cdn=True):
        serviceSpecs = {}
        for sla in self.slas:
            spec = self.serviceSpecFactory.fromSla(sla)
            if not include_cdn:
                spec.vcdn_count = 0
            serviceSpecs[sla] = spec

        return serviceSpecs

    def __init__(self, slas, serviceSpecFactory=ServiceSpecFactory):
        self.slas = slas
        self.serviceSpecFactory = serviceSpecFactory
        self.topo = {a: ServiceTopo(a, 3, 3) for a in self.slas}

    def __compute_vhg_vcdn_assignment__(self):

        sla_max_cdn_to_use = self.sla.max_cdn_to_use
        sla_node_specs = self.sla.sla_node_specs
        self.sla.max_cdn_to_use = 0
        self.sla.sla_node_specs = filter(lambda x: x.type == "cdn", self.sla.sla_node_specs)

        mapping = solve(self)
        if mapping is None:
            vhg_hints = None
        else:
            vhg_hints = mapping.get_vhg_mapping()

        self.sla.max_cdn_to_use = sla_max_cdn_to_use
        self.sla.sla_node_specs = sla_node_specs
        return vhg_hints

    def write(self):

        mode = "w"

        # write info on the edge
        with open(os.path.join(RESULTS_FOLDER, "service.edges.data"), mode) as f:
            for sla in self.slas:
                topo=self.topo[sla]
                for line in topo.dump_edges():
                    f.write(" ".join(str(a) for a in line) + "\n")
        with open(os.path.join(RESULTS_FOLDER, "service.nodes.data"), mode) as f:
            for sla in self.slas:
                topo = self.topo[sla]
                for line in topo.dump_nodes():
                    f.write(" ".join(str(a) for a in line) + "\n")





        # write path to associate e2e delay
        with open(os.path.join(RESULTS_FOLDER, "service.path.data"), mode) as f:
            for data in service_path:
                f.write("%s %s %s\n" % data)

        # write e2e delay constraint
        with open(os.path.join(RESULTS_FOLDER, "service.path.delay.data"), mode) as f:
            for x in set([i[0] for i in service_path]):
                f.write("%s %e\n" % (x, self.sla_delay))

        # write constraints on node capacity
        with open(os.path.join(RESULTS_FOLDER, "service.nodes.data"), mode) as f:
            f.write("S0_%s 0	\n" % self.id)
            self.spec.nodes["S0_%s" % self.id] = Node(0)
            for index, value in enumerate(self.start, start=1):
                f.write("S%d_%s 0	\n" % (index, self.id))
                self.spec.nodes["S%d_%s" % (index, self.id)] = Node(0)

            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d_%s 0\n" % (index, self.id))
                self.spec.nodes["CDN%d_%s" % (index, self.id)] = Node(0)

            if self.vhgcount > 1:
                for j in range(1, min(int(self.vcdncount) + 1, int(self.vhgcount) + 1)):
                    f.write("vCDN%d_%s	%e	\n" % (j, self.id, self.vcdncpu))
                    self.spec.nodes["vCDN%d_%s" % (j, self.id)] = Node(self.vcdncpu)
            else:  # can increase vcdn if vhg == 1
                for j in range(1, int(self.vcdncount) + 1):
                    f.write("vCDN%d_%s	%e	\n" % (j, self.id, self.vcdncpu))
                    self.spec.nodes["vCDN%d_%s" % (j, self.id)] = Node(self.vcdncpu)

            for i in range(1, int(self.vhgcount) + 1):
                f.write("VHG%d_%s %e\n" % (i, self.id, float(self.vhgcpu)))
                self.spec.nodes["VHG%d_%s" % (i, self.id)] = Node(float(self.vhgcpu))

        # write constraints on CDN placement
        with open(os.path.join(RESULTS_FOLDER, "CDN.nodes.data"), mode) as f:
            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d_%s %s\n" % (index, self.id, value.toponode_id))

        # write constraints on starter placement
        with open(os.path.join(RESULTS_FOLDER, "starters.nodes.data"), mode) as f:
            for index, value in enumerate(self.start, start=1):
                f.write("S%d_%s %s\n" % (index, self.id, value.toponode_id))

        # write constraints on the maximum amont of cdn to use
        with open(os.path.join(RESULTS_FOLDER, "cdnmax.data"), 'w') as f:
            f.write("%d" % self.max_cdn_to_use)

        # write the names of the VHG Nodes (is it still used?)
        with open(os.path.join(RESULTS_FOLDER, "VHG.nodes.data"), mode) as f:
            for index in range(1, self.vhgcount + 1):
                f.write("VHG%d_%s\n" % (index, self.id))

        # write the names of the VCDN nodes (is it still used?)
        with open(os.path.join(RESULTS_FOLDER, "VCDN.nodes.data"), mode) as f:
            for index in range(1, self.vcdncount + 1):
                f.write("vCDN%d_%s\n" % (index, self.id))
