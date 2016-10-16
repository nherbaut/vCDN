import collections
import copy
import logging

import networkx as nx
from networkx import shortest_path

from offline.core.service_topo import AbstractServiceTopo, get_all_possible_edges, get_nodes_by_type
from offline.core.topo_instance import TopoInstance
from offline.pricing.generator import get_vmg_calculator


class IsomorphicServiceException(BaseException):
    pass


class ServiceTopoFullGenerator(AbstractServiceTopo):
    def __init__(self, sla, vhg_count, vcdn_count, hint_node_mappings=None):
        super(ServiceTopoFullGenerator, self).__init__(sla, vhg_count, vcdn_count, hint_node_mappings)

    def compute_service_topo(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay,
                             hint_node_mappings=None):

        vhg_count = min(len(mapped_start_nodes), vhg_count)
        vcdn_count = min(vcdn_count, vhg_count)

        service_graph = nx.DiGraph()
        service_graph.add_node("S0", cpu=0, type="S0", name="S0")

        # add nodes
        for key, slaNodeSpec in enumerate(mapped_start_nodes, start=1):
            service_graph.add_node("S%d" % key, cpu=0, type="S", mapping=slaNodeSpec.topoNode.name,
                                   bandwidth=slaNodeSpec.attributes["bandwidth"], name="S%d" % key)

        for i in range(1, vhg_count + 1):
            service_graph.add_node("VHG%d" % i, type="VHG", ratio=1, name="VHG%d" % i)

        for i in range(1, vcdn_count + 1):
            service_graph.add_node("VCDN%d" % i, type="VCDN", cpu=0, delay=delay, ratio=0.35, name="VCDN%d" % i)

        for index, cdn in enumerate(mapped_cdn_nodes, start=1):
            service_graph.add_node("CDN%d" % index, type="CDN", cpu=0, ratio=0.65, name="CDN%d" % index)

        first = get_all_possible_edges([get_nodes_by_type("S", service_graph), get_nodes_by_type("VHG", service_graph),
                                        get_nodes_by_type("VCDN", service_graph)])

        last = get_all_possible_edges([get_nodes_by_type("VHG", service_graph),
                                       get_nodes_by_type("CDN", service_graph)])

        vmg_calc = get_vmg_calculator()
        # add edges
        edges_sets = []
        for elt in first:
            for new_elt in last:
                elt_copy = copy.copy(elt)
                elt_copy += (new_elt)
                edges_sets.append(elt_copy)

        services = []

        for t in edges_sets:
            try:
                serviceT = copy.deepcopy(service_graph)
                for edge in t:
                    serviceT.add_edge(edge[0], edge[1])

                for s in services:
                    if nx.is_isomorphic(s, serviceT, equal_nodes):
                        # print("removed an isomorph yay")
                        raise IsomorphicServiceException()

                services.insert(0, serviceT)
                workin_nodes = []
                for index, sla_node_spec in enumerate(mapped_start_nodes, start=1):
                    serviceT.node["S%d" % index]["bandwidth"] = sla_node_spec.attributes["bandwidth"]
                    workin_nodes.append("S%d" % index)

                while len(workin_nodes) > 0:
                    node = workin_nodes.pop()
                    bandwidth = serviceT.node[node].get("bandwidth", 0.0)
                    children = serviceT[node].items()
                    for subnode, data in children:
                        workin_nodes.append(subnode)
                        edge_bw = bandwidth / float(len(children)) * serviceT.node[subnode].get("ratio", 1.0)
                        serviceT[node][subnode]["bandwidth"] = edge_bw
                        serviceT.node[subnode]["bandwidth"] = serviceT.node[subnode].get("bandwidth", 0.0) + edge_bw

                # assign CPU according to Bandwidth
                for vhg in get_nodes_by_type("VHG", serviceT):
                    serviceT.node[vhg]["cpu"] = vmg_calc(serviceT.node[vhg]["bandwidth"])

                delay_path = {}
                delay_route = collections.defaultdict(lambda: [])
                for vcdn in get_nodes_by_type("VCDN", serviceT):
                    for s in get_nodes_by_type("S", serviceT):
                        try:
                            sp = shortest_path(serviceT, s, vcdn)
                            key = "_".join(sp)
                            delay_path[key] = delay
                            for i in range(len(sp) - 1):
                                delay_route[key].append((sp[i], sp[i + 1]))

                        except:
                            continue
                logging.debug("so far, %d services" % len(services))
                yield TopoInstance(serviceT, delay_path, delay_route, delay)
            except IsomorphicServiceException as e:
                pass


def equal_nodes(node1, node2):
    '''

    :param node1: a node from a vcdn service graph
    :param node2: a node from a vcdn service graph
    :return: True is nodes can be considered equal for isomorphic transformation
    '''
    if (node1["name"] == node2["name"]) or (node1["type"] == node2["type"]) and (
                    node1["type"] == "VHG" or node1["type"] == "VCDN"):
        logging.debug("%s is equal to %s" % (node1["name"], node2["name"]))
        return True
    else:
        logging.debug("%s is NOT equal to %s" % (node1["name"], node2["name"]))
        return False
