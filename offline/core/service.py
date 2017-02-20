import logging
import multiprocessing
import os
import sys
from collections import Counter
from multiprocessing.pool import ThreadPool

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy import and_
from sqlalchemy.orm import relationship

from offline.core.service_topo_heuristic import ServiceTopoHeuristic
from ..core.sla import Sla, SlaNodeSpec
from ..core.solver import solve
from ..time.persistence import ServiceNode, ServiceEdge, Base, service_to_sla
from ..time.persistence import Session

OPTIM_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../optim')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


def f(x):
    session = Session()
    slasIDS, vhg_count, vcdn_count, use_heuristic = x
    service = Service(slasIDS=slasIDS, serviceSpecFactory=ServiceSpecFactory, vhg_count=vhg_count,
                      vcdn_count=vcdn_count, use_heuristic=use_heuristic)
    session.add(service)
    return service.id


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
    sla_id = Column(Integer, ForeignKey("Sla.id"))
    vhg_count = Column(Integer, nullable=False)
    vcdn_count = Column(Integer, nullable=False)
    serviceNodes = relationship("ServiceNode", cascade="all")
    serviceEdges = relationship("ServiceEdge", cascade="all")
    slas = relationship("Sla", secondary=service_to_sla, back_populates="services", cascade="save-update")
    merged_sla = relationship("Sla", foreign_keys=[sla_id], cascade="all")
    mapping = relationship("Mapping", uselist=False, cascade="all", back_populates="service")

    # TODO: update
    def update_mapping(self):
        '''
        :return: updates the internal mapping of the service according to the updated list of SLAS
        '''
        session = Session()
        if self.mapping is None:
            raise AttributeError("no mapping found")

        # get the new merged sla
        merged_new = self.get_merged_sla(self.slas)

        # create the service topology from the new merged sla
        self.topo = ServiceTopoHeuristic(sla=merged_new, vhg_count=self.vhg_count,
                                         vcdn_count=self.vcdn_count, hint_node_mappings=self.mapping.node_mappings)

        # retreive info on the new service.
        edges_from_new_topo = {(node_1, node_2): bw for node_1, node_2, bw in self.topo.dump_edges()}
        nodes_from_new_topo = {node: cpu for node, cpu, bw in self.topo.getServiceNodes()}

        # update edge mapping topology, delete them if they are not present anymore
        for em in self.mapping.edge_mappings:
            edge = em.serviceEdge
            service_edge = (edge.node_1.name, edge.node_2.name)
            if service_edge in edges_from_new_topo:
                edge.bandwidth = edges_from_new_topo[service_edge]
            else:
                session.delete(em)
            session.flush()

        # **don't** update CPU, just remove VHG or VCDN if they are not present anymore.
        for nm in self.mapping.node_mappings:

            if nm.service_node.name not in nodes_from_new_topo:
                session.delete(nm)
                session.flush()
        # prune service edges
        for se in self.serviceEdges:
            if (se.node_1.name, se.node_2.name) not in edges_from_new_topo:
                session.delete(se)
                session.flush()

        # prune service nodes
        for sn in self.serviceNodes:
            if sn.name not in nodes_from_new_topo:
                session.delete(sn)
                session.flush()

        self.mapping.objective_function = self.mapping.get_objective_function()

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
        service_specs = {}
        for sla in self.slas:
            spec = self.serviceSpecFactory.fromSla(sla)
            if not include_cdn:
                spec.vcdn_count = 0
            service_specs[sla] = spec

        return service_specs

    @classmethod
    def get_merged_sla(cls, slas):
        session = Session()
        # create a dict that can accumulate
        merge_sla = Counter()
        # for every SLA
        min_delay = sys.float_info.max
        for sla in slas:
            # accumulate in the dict
            merge_sla += Counter({node.toponode_id: node.attributes["bandwidth"] for node in sla.get_start_nodes()})
            min_delay = min(sla.delay, min_delay)
        # create the node specs
        merge_sla_nodes_specs = []

        for key, value in merge_sla.items():
            merge_sla_nodes_specs.append(SlaNodeSpec(toponode_id=key, attributes={"bandwidth": value}, type="start"))

        for cdnNodeSpec in slas[0].get_cdn_nodes():
            merge_sla_nodes_specs.append(SlaNodeSpec(toponode_id=cdnNodeSpec.toponode_id, type="cdn"))

        # create the sla
        sla = Sla(sla_node_specs=merge_sla_nodes_specs, substrate=slas[0].substrate, delay=min_delay,
                  max_cdn_to_use=slas[0].max_cdn_to_use)

        session.add(sla)
        try:
            session.flush()
        except:
            e = sys.exc_info()[0]
            print(e)
        return sla

    @classmethod
    def get_optimal(cls, slas, serviceSpecFactory=ServiceSpecFactory, max_vhg_count=10, max_vcdn_count=10,
                    threads=multiprocessing.cpu_count() - 1, remove_service=True, use_heuristic=True):
        session = Session()
        threadpool = ThreadPool(threads)
        thread_param = []

        max_vhg_count = min(max_vhg_count,
                            len(set([nodes.topoNode.name for sla in slas for nodes in sla.get_start_nodes()])))
        max_vcdn_count = min(max_vhg_count, max_vcdn_count)

        logging.debug("----------Looking for optima solution to embed %s with max_vhg=%d and max_vcdn=%d" % (
            " ".join([str(sla.id) for sla in slas]), max_vhg_count, max_vcdn_count))

        best_cost = sys.float_info.max
        best_service = None

        for vhg_count in range(1, max_vhg_count + 1, ):
            for vcdn_count in range(1, min(vhg_count, max_vcdn_count) + 1):
                thread_param.append(([sla.id for sla in slas], vhg_count, vcdn_count, use_heuristic))

        # services = threadpool.map(f, thread_param)
        services = [f(x) for x in thread_param]
        services = session.query(Service).filter(Service.id.in_(services)).all()

        for service in services:
            if service.mapping is not None:
                # candidate!
                logging.debug(
                    "----------We have a candidate service with (%d,%d), with cost %lf" % (
                        service.vhg_count, service.vcdn_count, service.mapping.objective_function))
                if service.mapping.objective_function < best_cost:
                    best_cost = service.mapping.objective_function
                    best_service = service
                    logging.debug(
                        "its the best so far")
                    session.flush()
                    continue

        if best_service is None:
            raise ValueError("Cannot compute any successful service")

        for service in services:
            if service.id != best_service.id:
                if remove_service:
                    session.delete(service)
                    session.flush()

        return best_service

    def __init__(self, topo_instance, slasIDS, serviceSpecFactory=ServiceSpecFactory, vhg_count=1, vcdn_count=1,
                 use_heuristic=True):
        session = Session()

        self.slas = session.query(Sla).filter(Sla.id.in_(slasIDS)).all()
        self.vhg_count = vhg_count
        self.vcdn_count = vcdn_count
        self.merged_sla = self.get_merged_sla(self.slas)
        self.serviceSpecFactory = serviceSpecFactory
        self.topo = topo_instance

        for node, cpu, bw in self.topo.getServiceNodes():
            node = ServiceNode(name=node, cpu=cpu, sla_id=self.merged_sla.id, bw=bw)
            session.add(node)
            self.serviceNodes.append(node)

        for node_1, node_2, bandwidth in self.topo.getServiceEdges():
            snode_1 = session.query(ServiceNode).filter(
                and_(ServiceNode.sla_id == self.merged_sla.id, ServiceNode.service_id == self.id,
                     ServiceNode.name == node_1)).one()

            snode_2 = session.query(ServiceNode).filter(
                and_(ServiceNode.sla_id == self.merged_sla.id, ServiceNode.service_id == self.id,
                     ServiceNode.name == node_2)).one()

            sedge = ServiceEdge(node_1=snode_1, node_2=snode_2, bandwidth=bandwidth, sla_id=self.merged_sla.id)
            session.add(sedge)
            self.serviceEdges.append(sedge)
        session.flush()

        session.add(self)
        session.flush()
        if use_heuristic:

            # create temp mapping for vhg<->vcdn hints
            assert self.id is not None
            self.__solve(path=str(self.id), reopt=False)
            session.flush()

            if self.mapping is not None:
                self.topo = list(ServiceTopoHeuristic(sla=self.merged_sla, vhg_count=vhg_count, vcdn_count=vcdn_count,
                                                      hint_node_mappings=self.mapping.node_mappings).getTopos())[0]

                # add the CDN Edges to the graph
                for sla in [self.merged_sla]:

                    for node_1, node_2, bandwidth in self.topo.getServiceCDNEdges():
                        snode_1 = session.query(ServiceNode).filter(
                            and_(ServiceNode.sla_id == sla.id, ServiceNode.service_id == self.id,
                                 ServiceNode.name == node_1)).one()

                        snode_2 = session.query(ServiceNode).filter(
                            and_(ServiceNode.sla_id == sla.id, ServiceNode.service_id == self.id,
                                 ServiceNode.name == node_2)).one()

                        sedge = ServiceEdge(node_1=snode_1, node_2=snode_2, bandwidth=bandwidth, sla_id=sla.id)
                        session.add(sedge)
                        self.serviceEdges.append(sedge)
                    session.flush()

                session.delete(self.mapping)
                session.flush()

                self.__solve(path=str(self.id), use_heuristic=use_heuristic, reopt=True)
        else:
            return
            self.__solve(path=str(self.id), use_heuristic=use_heuristic, reopt=False)

        session.flush()

    def __solve(self, path=".", use_heuristic=True, reopt=False):
        """
        Solve the service according to specs
        :return: nothing, service.mapping may be initialized with an actual possible mapping
        """
        session = Session()
        if len(self.slas) > 0:
            solve(self, self.slas[0].substrate, path, use_heuristic, reopt)
            if self.mapping is not None:
                session.add(self.mapping)

            else:
                logging.warning("mapping failed for slas %s" % (" ".join(str(sla.id) for sla in self.slas)))

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

    def write(self, path="."):

        if not os.path.exists(os.path.join(RESULTS_FOLDER, path)):
            os.makedirs(os.path.join(RESULTS_FOLDER, path))

        mode = "w"
        # slas = self.slas
        slas = [self.merged_sla]

        # write info on the edge
        with open(os.path.join(RESULTS_FOLDER, path, "service.edges.data"), mode) as f:
            for sla in slas:
                postfix = "%d_%d" % (self.id, sla.id)
                for start, end, bw in self.topo.dump_edges():
                    f.write("%s\t\t%s_%s\t\t%lf\n" % (("%s_%s" % (start, postfix)).ljust(20), end, postfix, bw))

        with open(os.path.join(RESULTS_FOLDER, path, "service.nodes.data"), mode) as f:
            for sla in slas:
                postfix = "%d_%d" % (self.id, sla.id)

                for snode_id, cpu, bw in self.topo.getServiceNodes():
                    f.write("%s\t\t%lf\t\t%lf\n" % (("%s_%s" % (snode_id, postfix)).ljust(20), cpu, bw))
                    # sys.stdout.write("%s_%s %lf\n" % (snode_id, postfix, cpu))


                    # write constraints on CDN placement
        with open(os.path.join(RESULTS_FOLDER, path, "CDN.nodes.data"), mode) as f:
            for sla in slas:
                postfix = "%d_%d" % (self.id, sla.id)
                self.merged_sla.get_cdn_nodes()
                for node, mapping, bw in self.topo.get_CDN():
                    f.write("%s_%s %s\n" % (node, postfix, mapping))

        # write constraints on starter placement
        with open(os.path.join(RESULTS_FOLDER, path, "starters.nodes.data"), mode) as f:
            for sla in slas:
                postfix = "%d_%d" % (self.id, sla.id)
                for s, topo, bw in self.topo.get_Starters():
                    f.write("%s_%s %s %lf\n" % (s, postfix, topo, bw))

        # write the names of the VHG Nodes
        with open(os.path.join(RESULTS_FOLDER, path, "VHG.nodes.data"), mode) as f:
            for sla in slas:
                postfix = "%d_%d" % (self.id, sla.id)
                for vhg in self.topo.get_vhg():
                    f.write("%s_%s\n" % (vhg, postfix))

        # write the names of the VCDN nodes
        with open(os.path.join(RESULTS_FOLDER, path, "VCDN.nodes.data"), mode) as f:
            for sla in slas:
                postfix = "%d_%d" % (self.id, sla.id)
                for vcdn in self.topo.get_vcdn():
                    f.write("%s_%s\n" % (vcdn, postfix))

                    # write path to associate e2e delay

        with open(os.path.join(RESULTS_FOLDER, path, "service.path.delay.data"), "w") as f:
            for sla in slas:
                postfix = "%d_%d" % (self.id, sla.id)

                for apath in self.topo.dump_delay_paths():
                    f.write("%s_%s %lf\n" % (apath, postfix, self.topo.delay))

        # write e2e delay constraint
        with open(os.path.join(RESULTS_FOLDER, path, "service.path.data"), "w") as f:
            for sla in slas:
                postfix = "%d_%d" % (self.id, sla.id)

                for apath, s1, s2 in self.topo.dump_delay_routes():
                    f.write("%s_%s %s_%s %s_%s\n" % (apath, postfix, s1, postfix, s2, postfix))

    @classmethod
    def getFromSla(cls, sla):
        session = Session()
        return session.query(Service).filter(Sla.id == sla.id).join(Service.slas).filter(Sla.id == sla.id).one()
