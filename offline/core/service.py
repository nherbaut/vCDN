from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from ..core.service_topo import ServiceTopo
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

    def __init__(self, slas, serviceSpecFactory=ServiceSpecFactory, slas_spec={}):
        self.slas = slas
        self.serviceSpecFactory = serviceSpecFactory


        self.topo= {sla: ServiceTopo(sla=sla, vhg_count=slas_spec.get(sla.id, {}).get("vhg", 1),
                                      vcdn_count=slas_spec.get(sla.id, {}).get("vcdn", 1), hint_mapping=None) for sla in self.slas}


        hint_mapping=self.solve()
        self.topo= {sla: ServiceTopo(sla=sla, vhg_count=slas_spec.get(sla.id, {}).get("vhg", 1),
                                      vcdn_count=slas_spec.get(sla.id, {}).get("vcdn", 1), hint_mapping=hint_mapping)
                     for sla in
                     self.slas}

    def solve(self):
        return solve(self, self.slas[0].substrate)

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
                topo = self.topo[sla]
                for line in topo.dump_edges():
                    f.write(" ".join(str(a) for a in line) + "\n")
        with open(os.path.join(RESULTS_FOLDER, "service.nodes.data"), mode) as f:
            for sla in self.slas:
                topo = self.topo[sla]
                for line in topo.dump_nodes():
                    f.write(" ".join(str(a) for a in line) + "\n")

        # write constraints on CDN placement
        with open(os.path.join(RESULTS_FOLDER, "CDN.nodes.data"), mode) as f:
            for sla in self.slas:
                for index, value in enumerate(sla.get_cdn_nodes(), start=1):
                    f.write("CDN%d_%s %s\n" % (index, sla.id, value.toponode_id))

        # write constraints on starter placement
        with open(os.path.join(RESULTS_FOLDER, "starters.nodes.data"), mode) as f:
            for sla in self.slas:
                for index, value in enumerate(sla.get_start_nodes(), start=1):
                    f.write("S%d_%s %s\n" % (index, sla.id, value.toponode_id))

        # write the names of the VHG Nodes
        with open(os.path.join(RESULTS_FOLDER, "VHG.nodes.data"), mode) as f:
            for sla in self.slas:
                for index in range(1, len(sla.get_start_nodes()) + 1):
                    f.write("VHG%d_%s\n" % (index, sla.id))

        # write the names of the VCDN nodes (is it still used?)
        with open(os.path.join(RESULTS_FOLDER, "VCDN.nodes.data"), mode) as f:
            for sla in self.slas:
                for index in range(1, len(sla.get_cdn_nodes()) + 1):
                    f.write("vCDN%d_%s\n" % (index, sla.id))

                    # write path to associate e2e delay

        with open(os.path.join(RESULTS_FOLDER, "service.path.delay.data"), "w") as f:
            for sla in self.slas:
                topo = self.topo[sla]
                for data in topo.dump_delay_paths():
                    f.write("%s\n" % data)

        # write e2e delay constraint
        with open(os.path.join(RESULTS_FOLDER, "service.path.data"), "w") as f:
            for sla in self.slas:
                topo = self.topo[sla]
                for data in topo.dump_delay_routes():
                    f.write("%s\n" % data)
