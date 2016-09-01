from sqlalchemy import Column, Integer
from sqlalchemy import and_
from sqlalchemy.orm import relationship

from ..core.service_topo import ServiceTopo
from ..core.sla import Sla
from ..core.solver import solve
from ..time.persistence import *

OPTIM_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../optim')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


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
    slas = relationship("Sla", secondary=service_to_sla, back_populates="services",cascade="save-update")
    mapping = relationship("Mapping", uselist=False,cascade="all", back_populates="service")

    def update_mapping(self):

        for em in self.mapping.edge_mappings:
            if em.serviceEdge.sla not in self.slas:
                session.delete(em)
                session.flush()


        for nm in self.mapping.node_mappings:
            if nm.sla not in self.slas:
                session.delete(nm)
                session.flush()

        for se in self.serviceEdges:
            if se.sla not in self.slas:

                session.delete(se)
                session.flush()

        for sn in self.serviceNodes:
            if sn.sla not in self.slas:
                session.delete(sn)
                session.flush()

        self.mapping.objective_function = self.mapping.get_objective_function(cpu_cost=self.slas[0].substrate.cpuCost,net_cost=self.slas[0].substrate.netCost)

    def __str__(self):
        return str(self.id) + " - " + " ".join([str(sla.id) for sla in self.slas])

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

        self.topo = {sla: ServiceTopo(sla=sla, vhg_count=slas_spec.get(sla.id, {}).get("VHG", 1),
                                      vcdn_count=slas_spec.get(sla.id, {}).get("VCDN", 1), hint_node_mappings=None) for
                     sla in
                     self.slas}

        for sla in slas:
            for node, cpu in self.topo[sla].getServiceNodes():
                node = ServiceNode(node_id=node, cpu=cpu, sla_id=sla.id)
                session.add(node)
                self.serviceNodes.append(node)

            for node_1, node_2, bandwidth in self.topo[sla].getServiceEdges():
                snode_1 = session.query(ServiceNode).filter(
                    and_(ServiceNode.sla_id == sla.id, ServiceNode.service_id == self.id,
                         ServiceNode.node_id == node_1)).one()

                snode_2 = session.query(ServiceNode).filter(
                    and_(ServiceNode.sla_id == sla.id, ServiceNode.service_id == self.id,
                         ServiceNode.node_id == node_2)).one()

                sedge = ServiceEdge(node_1=snode_1, node_2=snode_2, bandwidth=bandwidth, sla_id=sla.id)
                session.add(sedge)
                self.serviceEdges.append(sedge)
            session.flush()

        # create temp mapping for vhg<->vcdn hints
        self.solve()
        session.flush()

        if self.mapping is not None:
            self.topo = {sla: ServiceTopo(sla=sla, vhg_count=slas_spec.get(sla.id, {}).get("vhg", 1),
                                          vcdn_count=slas_spec.get(sla.id, {}).get("vcdn", 1),
                                          hint_node_mappings=self.mapping.node_mappings) for sla in self.slas}
            # remove temp mapping for vhg<->vcdn hints
            # for em in self.mapping.edge_mappings:
            #    session.delete(em)
            #    session.flush()
            # for nm in self.mapping.node_mappings:
            #    session.delete(nm)
            #   session.flush()
            session.delete(self.mapping)
            session.flush()

    def solve(self):
        if len(self.slas) > 0:
            solve(self, self.slas[0].substrate)
            if self.mapping is not None:
                session.add(self.mapping)

            else:
                print
                "mapping failed"

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
                postfix = "%d_%d" % (self.id, sla.id)
                topo = self.topo[sla]
                for start, end, bw in topo.dump_edges():
                    f.write("%s_%s %s_%s %lf\n" % (start, postfix, end, postfix, bw))

        with open(os.path.join(RESULTS_FOLDER, "service.nodes.data"), mode) as f:
            for sla in self.slas:
                postfix = "%d_%d" % (self.id, sla.id)
                topo = self.topo[sla]
                for snode_id, cpu in topo.dump_nodes():
                    f.write("%s_%s %lf\n" % (snode_id, postfix, cpu))
                    # sys.stdout.write("%s_%s %lf\n" % (snode_id, postfix, cpu))




                    # write constraints on CDN placement
        with open(os.path.join(RESULTS_FOLDER, "CDN.nodes.data"), mode) as f:
            for sla in self.slas:
                postfix = "%d_%d" % (self.id, sla.id)
                for index, value in enumerate(sla.get_cdn_nodes(), start=1):
                    f.write("CDN%d_%s %s\n" % (index, postfix, value.toponode_id))

        # write constraints on starter placement
        with open(os.path.join(RESULTS_FOLDER, "starters.nodes.data"), mode) as f:
            for sla in self.slas:
                postfix = "%d_%d" % (self.id, sla.id)
                for s, topo in self.topo[sla].get_Starters():
                    f.write("%s_%s %s\n" % (s, postfix, topo))

        # write the names of the VHG Nodes
        with open(os.path.join(RESULTS_FOLDER, "VHG.nodes.data"), mode) as f:
            for sla in self.slas:
                postfix = "%d_%d" % (self.id, sla.id)
                for vhg in self.topo[sla].get_vhg():
                    f.write("%s_%s %e\n" % (vhg, postfix,self.get_vhg_cost(vhg)))

        # write the names of the VCDN nodes (is it still used?)
        with open(os.path.join(RESULTS_FOLDER, "VCDN.nodes.data"), mode) as f:
            for sla in self.slas:
                postfix = "%d_%d" % (self.id, sla.id)
                for vcdn in self.topo[sla].get_vcdn():
                    f.write("%s_%s %e\n" % (vcdn, postfix,self.get_vcdn_cost(vcdn)))

                    # write path to associate e2e delay

        with open(os.path.join(RESULTS_FOLDER, "service.path.delay.data"), "w") as f:
            for sla in self.slas:
                postfix = "%d_%d" % (self.id, sla.id)
                topo = self.topo[sla]
                for path, delay in topo.dump_delay_paths():
                    f.write("%s_%s %lf\n" % (path, postfix, delay))

        # write e2e delay constraint
        with open(os.path.join(RESULTS_FOLDER, "service.path.data"), "w") as f:
            for sla in self.slas:
                postfix = "%d_%d" % (self.id, sla.id)
                topo = self.topo[sla]
                for path, s1, s2 in topo.dump_delay_routes():
                    f.write("%s_%s %s_%s %s_%s\n" % (path, postfix, s1, postfix, s2, postfix))

    @classmethod
    def getFromSla(cls, sla):
        return session.query(Service).filter(Sla.id == sla.id).join(Service.slas).filter(Sla.id == sla.id).one()



    def get_vhg_cost(self,vhg):
        return 1

    def get_vcdn_cost(self,vcdn):
        return 1