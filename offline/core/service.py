import logging
import multiprocessing
import os
import sys
import traceback
from collections import Counter
from multiprocessing.pool import ThreadPool


# Shortcut to multiprocessing's logger
def error(msg, *args):
    return multiprocessing.get_logger().error(msg, *args)


class LogExceptions(object):
    def __init__(self, callable):
        self.__callable = callable

    def __call__(self, *args, **kwargs):
        try:
            result = self.__callable(*args, **kwargs)

        except Exception as e:
            # Here we add some debugging help. If multiprocessing's
            # debugging is on, it will arrange to log the traceback
            error(traceback.format_exc())
            # Re-raise the original exception so the Pool worker can
            # clean up
            raise

        # It was fine, give a normal answer
        return result


class LoggingPool(ThreadPool):
    def map(self, func, iterable, chunksize=None):
        '''
        Equivalent of `map()` builtin
        '''
        assert self._state == RUN
        print("coucoucoucou")
        return ThreadPool.map_async(self, LogExceptions(func), iterable, chunksize).get()


from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from offline.core.reduced_service_graph_generator import HeuristicServiceGraphGenerator
from ..core.sla import Sla, SlaNodeSpec
from ..time.persistence import ServiceNode, ServiceEdge, Base
from ..time.persistence import Session

OPTIM_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../optim')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


def f(x):
    session = Session()
    slasIDS, vhg_count, vcdn_count, use_heuristic = x
    service = Service(slasIDS=slasIDS, serviceSpecFactory=ServiceSpecFactory, vhg_count=vhg_count,
                      vcdn_count=vcdn_count, use_heuristic=use_heuristic)

    # session.add(service)
    return service.id


def get_count_by_type(self, type):
    return [x for x in self.servicetopo.edges_iter(data=True) if x[2]["type"] == 'x']


def get_vhg_count(self):
    return len(self.get_count_by_type("VHG"))


def get_vcdn_count(self):
    return len(self.get_count_by_type("VCDN"))


class Service(Base):
    __tablename__ = "Service"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sla_id = Column(Integer, ForeignKey("Sla.id"))
    serviceNodes = relationship("ServiceNode", cascade="all")
    serviceEdges = relationship("ServiceEdge", cascade="all")
    # slas = relationship("Sla", secondary=service_to_sla, back_populates="services", cascade="save-update")
    sla = relationship("Sla", foreign_keys=[sla_id], back_populates="services", cascade="save-update")
    mapping = relationship("Mapping", uselist=False, cascade="all", back_populates="service")

    def __str__(self):
        return str(self.id) + " - " + " ".join([str(sla.id) for sla in self.slas])

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

        for key, value in list(merge_sla.items()):
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
    def get_optimal(cls, slas, max_vhg_count=10, max_vcdn_count=10,
                    threads=multiprocessing.cpu_count() - 1, remove_service=True, use_heuristic=True):
        session = Session()
        threadpool = LoggingPool(threads)
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

        services = threadpool.map(f, thread_param)
        # services = [f(x) for x in thread_param]
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

    def __init__(self, service_graph, sla, solver):
        self.sla = sla
        self.service_graph = service_graph
        self.solver = solver
        # print("%s"%self.service_graph)
        # copy stuff from the service_graph down to the Service itself for solving
        for node, cpu, bw in self.service_graph.get_service_nodes():
            snode = ServiceNode(name=node, cpu=cpu, sla_id=self.sla.id, bw=bw)
            self.serviceNodes.append(snode)
        for node_1, node_2, bandwidth in self.service_graph.get_service_edges():
            snode_1 = next(x for x in self.serviceNodes if x.sla_id == self.sla.id and x.name == node_1)
            snode_2 = next(x for x in self.serviceNodes if x.sla_id == self.sla.id and x.name == node_2)

            sedge = ServiceEdge(node_1=snode_1, node_2=snode_2, bandwidth=bandwidth, sla_id=self.sla.id,
                                service_id=self.id)
            self.serviceEdges.append(sedge)

    def solve(self):
        """
        Solve the service according to specs
        :return: nothing, service.mapping may be initialized with an actual possible mapping
        """
        self.solver.solve(self, self.sla.substrate)
        if self.mapping is None:
            logging.warning("mapping failed for sla %s" % self.sla.id)


    def __compute_vhg_vcdn_assignment__(self):

        sla_max_cdn_to_use = self.sla.max_cdn_to_use
        sla_node_specs = self.sla.sla_node_specs
        self.sla.max_cdn_to_use = 0
        self.sla.sla_node_specs = [x for x in self.sla.sla_node_specs if x.type == "cdn"]

        mapping = self.solver.solve(self)
        if mapping is None:
            vhg_hints = None
        else:
            vhg_hints = mapping.get_vhg_mapping()

        self.sla.max_cdn_to_use = sla_max_cdn_to_use
        self.sla.sla_node_specs = sla_node_specs
        return vhg_hints

    @classmethod
    def getFromSla(cls, sla):
        session = Session()
        return session.query(Service).filter(Sla.id == sla.id).join(Service.slas).filter(Sla.id == sla.id).one()

    # TODO: update refactor with new class scheme
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
        self.service_graph = HeuristicServiceGraphGenerator(sla=merged_new, vhg_count=self.vhg_count,
                                                            vcdn_count=self.vcdn_count,
                                                            hint_node_mappings=self.mapping.node_mappings)

        # retreive info on the new service.
        edges_from_new_topo = {(node_1, node_2): bw for node_1, node_2, bw in self.service_graph.dump_edges()}
        nodes_from_new_topo = {node: cpu for node, cpu, bw in self.service_graph.getServiceNodes()}

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

        self.mapping.objective_function = self.mapping.__get_objective_function()
