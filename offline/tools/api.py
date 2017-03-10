#!/usr/bin/env python3

import logging
import multiprocessing
import os
import re
from multiprocessing.pool import ThreadPool

import numpy as np
from numpy.random import RandomState
from sqlalchemy.orm.session import make_transient

from ..core.full_service_gaph_generator import FullServiceGraphGenerator
from ..core.ilpsolver import ILPSolver
from ..core.reduced_service_graph_generator import HeuristicServiceGraphGenerator
from ..core.service import Service
from ..core.sla import Sla, SlaNodeSpec
from ..core.sla import weighted_shuffle
from ..core.substrate import Substrate
from ..time.persistence import Session, Base, engine, drop_all, Tenant, Node

GEANT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/Geant2012.graphml')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

candidate_count = 0


def generate_sla_nodes(su, start, cdn, rs):
    '''
    return a list of nodes from a substrate and some specs
    :param su: the physical substrate
    :param start: list of node ids as str of 1 string like "RAND(n,m)"
    :param cdn: list of node ids as str of 1 string like "RAND(n,m)"
    :param rs: randomset
    :return: start_nodes, cdn_nodes
    '''

    start_nodes = None
    if len(start) == 1:
        match = re.findall("RAND\(([0-9]+),([0-9]+)\)", start[0])
        if len(match) == 1:
            nodes_by_bw = su.get_nodes_by_bw()
            size = rs.randint(int(match[0][0]), int(match[0][1]) + 1)
            start_nodes = weighted_shuffle(list(nodes_by_bw.keys()), list(nodes_by_bw.values()), size, rs)
            logging.debug("random start nodes: %s" % " ".join(start_nodes))

    cdn_nodes = None
    if len(cdn) == 1:
        match = re.findall("RAND\(([0-9]+),([0-9]+)\)", cdn[0])
        if len(match) == 1:
            nodes_by_degree = su.get_nodes_by_degree()
            # remove starters from possible cdn list
            for sn in start_nodes:
                nodes_by_degree.pop(sn, None)
            size = rs.randint(int(match[0][0]), int(match[0][1]) + 1)
            cdn_nodes = weighted_shuffle(list(nodes_by_degree.keys()),
                                         -1.0 * np.array(list(nodes_by_degree.values())), size, rs)
            logging.debug("random cdn nodes: %s" % " ".join(cdn_nodes))

    if start_nodes is None:
        start_nodes = start

    if cdn_nodes is None:
        cdn_nodes = cdn

    return start_nodes, cdn_nodes


def clean_and_create_experiment(topo=('file', ('Geant2012.graphml', '10000')), seed=0):
    '''

    :param topo: the topology generated according to specs
    :param seed: the randomset used for generation
    :return: rs, substrate
    '''

    Base.metadata.create_all(engine)
    drop_all()

    rs = RandomState(seed)
    su = Substrate.fromSpec(topo, rs)
    return rs, su


def embbed_service(args):
    session = Session()
    service_graph, sla_id = args
    sla = session.query(Sla).filter(Sla.id == sla_id).one()
    service = Service(service_graph, sla, solver=ILPSolver())
    service.solve()
    global candidate_count
    candidate_count += 1
    return service


def create_sla(starts, cdns, sourcebw, topo=None, su=None, seed=0):
    if su is None:
        _, su = clean_and_create_experiment(topo, seed)

    nodes_names = [n.name for n in su.nodes]
    session = Session()

    for s in starts:
        assert s in nodes_names, "%s not in %s" % (s, nodes_names)

    if len(cdns) == 1 and cdns[0] == "all":
        cdns = [node.name for node in su.nodes]

    for s in cdns:
        assert s in nodes_names, "%s not in %s" % (s, nodes_names)

    session.add(su)
    session.flush()

    tenant = Tenant()
    session.add(tenant)

    sla_node_specs = []
    bw_per_s = sourcebw / float(len(starts))
    for start in starts:
        ns = SlaNodeSpec(topoNode=session.query(Node).filter(Node.name == start).one(), type="start",
                         attributes={"bandwidth": bw_per_s})
        sla_node_specs.append(ns)

    for cdn in cdns:
        ns = SlaNodeSpec(topoNode=session.query(Node).filter(Node.name == cdn).one(), type="cdn",
                         attributes={"bandwidth": 1})
        sla_node_specs.append(ns)

    sla = Sla(substrate=su, delay=200, max_cdn_to_use=1, tenant_id=tenant.id, sla_node_specs=sla_node_specs)
    session.add(sla)
    session.flush()

    return sla


class ServiceGraphGeneratorFactory:
    '''
    A factory to ease the creation of servie graph
    '''

    def __init__(self, sla, automatic=True, vhg_count=None, vcdn_count=None):
        self.sla = sla
        self.automatic = automatic
        self.vhg_count = vhg_count
        self.vcdn_count = vcdn_count
        assert (self.automatic and (self.vhg_count is None and self.vcdn_count is None)) or (
            not self.automatic and (self.vhg_count is not None and self.vcdn_count is not None))

    def get_reduced_class_generator(self, solver, max_vhg_count=10, max_vcdn_count=10):

        if self.automatic is False:
            return [HeuristicServiceGraphGenerator(sla=self.sla, vhg_count=self.vhg_count, vcdn_count=self.vcdn_count,
                                                   solver=solver)]
        else:
            topo_containers = []
            for vhg_count in range(1, min(max_vhg_count, len(self.sla.get_start_nodes())) + 1):
                for vcdn_count in range(1, min(max_vcdn_count, vhg_count) + 1):
                    topo_container = HeuristicServiceGraphGenerator(sla=self.sla, vhg_count=vhg_count,
                                                                    vcdn_count=vcdn_count, solver=solver)
                    topo_containers.append(topo_container)
            return topo_containers

    def get_full_class_generator(self, ):
        if self.automatic is True:
            return self.__get_full_class_generator_automatic(disable_isomorph_check=True)
        else:
            return [FullServiceGraphGenerator(sla=self.sla, vhg_count=self.vhg_count, vcdn_count=self.vcdn_count,
                                              disable_isomorph_check=True)]

    def get_full_class_generator_filtered(self, ):
        if self.automatic is True:
            return self.__get_full_class_generator_automatic(disable_isomorph_check=False)
        else:
            return [FullServiceGraphGenerator(sla=self.sla, vhg_count=self.vhg_count, vcdn_count=self.vcdn_count,
                                              disable_isomorph_check=False)]

    def __get_full_class_generator_automatic(self, disable_isomorph_check=True):
        topo_containers = []
        for vhg_count in range(1, len(self.sla.get_start_nodes()) + 1):
            for vcdn_count in range(1, vhg_count + 1):
                topo_container = FullServiceGraphGenerator(sla=self.sla, vhg_count=vhg_count,
                                                           vcdn_count=vcdn_count,
                                                           disable_isomorph_check=disable_isomorph_check)
                topo_containers.append(topo_container)
        return topo_containers


def optimize_sla(sla, vhg_count=None, vcdn_count=None,
                 automatic=True, use_heuristic=True, isomorph_check=True,
                 max_vhg_count=10, max_vcdn_count=100, solver=ILPSolver()):
    factory = ServiceGraphGeneratorFactory(sla, automatic, vhg_count=vhg_count, vcdn_count=vcdn_count)
    if use_heuristic:
        generators = factory.get_reduced_class_generator(solver=solver, max_vhg_count=max_vhg_count,
                                                         max_vcdn_count=max_vcdn_count)
    else:
        if isomorph_check:
            generators = factory.get_full_class_generator_filtered()
        else:
            generators = factory.get_full_class_generator()

    candidates_param = [(topo, sla.id) for generator in generators for topo in generator.get_service_topologies()]
    logging.debug("%d candidate " % len(candidates_param))

    # sys.stdout.write("\n\t Service to embed :%d\n" % len(candidates_param))

    # print("%d param to optimize" % len(candidates_param))
    pool = ThreadPool(multiprocessing.cpu_count() - 1)
    # sys.stdout.write("\n\t Embedding services:%d\n" % len(candidates_param))
    services = pool.map(embbed_service, candidates_param)

    # services = [embbed_service(param) for param in candidates_param]
    # sys.stdout.write(" done!\n")

    services = [x for x in services if x.mapping is not None]
    services = sorted(services, key=lambda x: x.mapping.objective_function, )

    for service in services:
        logging.debug(
            "%d %lf %d %d" % (service.id, service.mapping.objective_function, service.service_graph.get_vhg_count(),
                              service.service_graph.get_vcdn_count()))

    if len(services) > 0:
        winner = services[0]
        return winner, candidate_count
    else:
        raise ValueError("failed to compute valide mapping")


def create_adhoc_sla(sla, service_graph):
    session = Session()
    su = Substrate.from_service_graph(service_graph)
    for mapped_node in service_graph.get_cdn()+service_graph.get_starters():
        service_graph.set_node_mapping(mapped_node,mapped_node)
    session.add(su)
    session.expunge(sla)
    make_transient(sla)
    sla.substrate = su
    sla.id = None
    session.add(sla)
    session.flush()

    return sla


def optimize_sla_benchmark(sla, vhg_count=None, vcdn_count=None,
                           automatic=True, use_heuristic=True, isomorph_check=True,
                           max_vhg_count=10, max_vcdn_count=100, solver=ILPSolver()):
    factory = ServiceGraphGeneratorFactory(sla, automatic, vhg_count=vhg_count, vcdn_count=vcdn_count)
    if use_heuristic:
        generators = factory.get_reduced_class_generator(solver=solver, max_vhg_count=max_vhg_count,
                                                         max_vcdn_count=max_vcdn_count)
    else:
        if isomorph_check:
            generators = factory.get_full_class_generator_filtered()
        else:
            generators = factory.get_full_class_generator()

    candidates_param = [(topo, sla.id) for generator in generators for topo in generator.get_service_topologies()]

    #candidates_param = [(topo, create_adhoc_sla(sla, topo).id) for topo, sla in candidates_param]
    #candidates_param = [(topo, create_adhoc_sla(sla,topo).id) for generator in generators for topo in generator.get_service_topologies()]
    logging.debug("%d candidate " % len(candidates_param))

    # sys.stdout.write("\n\t Service to embed :%d\n" % len(candidates_param))

    # print("%d param to optimize" % len(candidates_param))
    # pool = ThreadPool(multiprocessing.cpu_count() - 1)
    # sys.stdout.write("\n\t Embedding services:%d\n" % len(candidates_param))
    # services = pool.map(embbed_service, candidates_param)

    services = [embbed_service(param) for param in candidates_param]
    # sys.stdout.write(" done!\n")

    services = [x for x in services if x.mapping is not None]
    services = sorted(services, key=lambda x: x.mapping.objective_function, )

    for service in services:
        logging.debug(
            "%d %lf %d %d" % (service.id, service.mapping.objective_function, service.service_graph.get_vhg_count(),
                              service.service_graph.get_vcdn_count()))

    if len(services) > 0:
        winner = services[0]
        return winner, candidate_count
    else:
        raise ValueError("failed to compute valid mapping")
