import collections
import copy

import networkx as nx
from networkx import shortest_path

from offline.core.service_graph_generator import AbstractServiceGraphGenerator, get_all_possible_edges, get_nodes_by_type
from offline.core.service_graph import ServiceGraph
from offline.pricing.generator import get_vmg_calculator, get_vcdn_calculator


class IsomorphicServiceException(BaseException):
    pass


class FullServiceGraphGenerator(AbstractServiceGraphGenerator):
    def __init__(self, sla, vhg_count=None, vcdn_count=None, hint_node_mappings=None, disable_isomorph_check=False):
        self.disable_isomorph_check = disable_isomorph_check
        super(FullServiceGraphGenerator, self).__init__(sla, vhg_count, vcdn_count, hint_node_mappings)

    def compute_service_topos(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay):

        accepted_service_graphs = []

        vhg_count = min(len(mapped_start_nodes), vhg_count)
        vcdn_count = min(vcdn_count, vhg_count)

        service_graph = nx.DiGraph()

        # add nodes
        for key, slaNodeSpec in enumerate(mapped_start_nodes, start=1):
            service_graph.add_node("S%d" % key, cpu=0, type="S", mapping=slaNodeSpec.topoNode.name,
                                   bandwidth=slaNodeSpec.attributes["bandwidth"], name="S%d" % key, ratio=1)

        for i in range(1, vhg_count + 1):
            service_graph.add_node("VHG%d" % i, type="VHG", ratio=1, name="VHG%d" % i, bandwidth=0)

        for i in range(1, vcdn_count + 1):
            service_graph.add_node("VCDN%d" % i, type="VCDN", cpu=105, delay=delay, ratio=0.35, name="VCDN%d" % i,
                                   bandwidth=0)

        for index, cdn in enumerate(mapped_cdn_nodes, start=1):
            service_graph.add_node("CDN%d" % index, type="CDN", cpu=0, ratio=0.65, name="CDN%d" % index, bandwidth=0,
                                   mapping=cdn.topoNode.name)

        first = get_all_possible_edges([get_nodes_by_type("S", service_graph), get_nodes_by_type("VHG", service_graph),
                                        get_nodes_by_type("VCDN", service_graph)])

        last = get_all_possible_edges([get_nodes_by_type("VHG", service_graph),
                                       get_nodes_by_type("CDN", service_graph)], all_rights_are_mandatory=False)

        vmg_calc = get_vmg_calculator()
        vcdn_calc = get_vcdn_calculator()
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
                service_graph_clone = copy.deepcopy(service_graph)
                for edge in t:
                    service_graph_clone.add_edge(edge[0], edge[1])

                for node, degree in list(service_graph_clone.degree().items()):
                    if degree == 0:
                        service_graph_clone.remove_node(node)

                str_rep = "-".join(
                    sorted(["%s_%s" % (t[0], t[1].get("mapping", "NA")) for t in service_graph_clone.nodes(data=True)]))
                # print str_rep
                # sys.stdout.write("o")
                # sys.stdout.flush()
                if not self.disable_isomorph_check:
                    for s in services:
                        if "-".join(sorted(
                                ["%s_%s" % (t[0], t[1].get("mapping", "NA")) for t in s.nodes(data=True)])) == str_rep:
                            if nx.is_isomorphic(s, service_graph_clone, equal_nodes):
                                # sys.stdout.write("\b")
                                # sys.stdout.flush()
                                raise IsomorphicServiceException()

                # sys.stdout.write("\bO")
                # sys.stdout.flush()

                services.insert(0, service_graph_clone)

                self.propagate_bandwidth(service_graph_clone, mapped_start_nodes=mapped_start_nodes)

                # assign CPU according to Bandwidth
                for vhg in get_nodes_by_type("VHG", service_graph_clone):
                    service_graph_clone.node[vhg]["cpu"] = vmg_calc(service_graph_clone.node[vhg]["bandwidth"])

                for vhg in get_nodes_by_type("VCDN", service_graph_clone):
                    service_graph_clone.node[vhg]["cpu"] = vcdn_calc(service_graph_clone.node[vhg]["bandwidth"])

                delay_path = {}
                delay_route = collections.defaultdict(lambda: [])
                for vcdn in get_nodes_by_type("VCDN", service_graph_clone):
                    for s in get_nodes_by_type("S", service_graph_clone):
                        try:
                            sp = shortest_path(service_graph_clone, s, vcdn)
                            key = "_".join(sp)
                            delay_path[key] = delay
                            for i in range(len(sp) - 1):
                                delay_route[key].append((sp[i], sp[i + 1]))

                        except:
                            continue
                # logging.debug("so far, %d services" % len(services))

                accepted_service_graphs.append(service_graph_clone)

                #print("Matrix:\n%s\n\n"%nx.adjacency_matrix(service_graph_clone))
                yield [ServiceGraph(service_graph_clone, delay_path, delay_route, delay)]

            except IsomorphicServiceException as e:
                pass


def equal_nodes(node1, node2):
    '''

    :param node1: a node from a vcdn service graph
    :param node2: a node from a vcdn service graph
    :return: True is nodes can be considered equal for isomorphic transformation
    '''

    if (node1["name"] == node2["name"]) or ((node1["type"] == node2["type"]) and (
                    node1["type"] == "VHG" or node1["type"] == "VCDN")):
        return True
    else:
        return False
