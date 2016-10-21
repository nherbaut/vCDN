import copy
import sys

import networkx as nx


class AbstractServiceTopo(object):
    def __init__(self, sla, vhg_count, vcdn_count, hint_node_mappings=None):
        mapped_start_nodes = sla.get_start_nodes()
        mapped_cdn_nodes = sla.get_cdn_nodes()
        self.sla_id = sla.id
        self.topoinfos = list(self.compute_service_topo(
            mapped_start_nodes=mapped_start_nodes, mapped_cdn_nodes=mapped_cdn_nodes, vhg_count=vhg_count,
            vcdn_count=vcdn_count, delay=sla.delay,
            hint_node_mappings=hint_node_mappings, substrate=sla.substrate, ))

    def getTopos(self):
        return self.topoinfos

    def propagate_bandwidth(self, service, mapped_start_nodes):
        # assign bandwidth
        workin_nodes = []
        for index, sla_node_spec in enumerate(mapped_start_nodes, start=1):
            service.node["S%d" % index]["bandwidth"] = sla_node_spec.attributes["bandwidth"]
            workin_nodes.append("S%d" % index)

        while len(workin_nodes) > 0:
            node = workin_nodes.pop()
            bandwidth = service.node[node].get("bandwidth", 0.0)
            children = service[node].items()
            for subnode, data in children:
                workin_nodes.append(subnode)
                edge_bw = bandwidth * service.node[subnode]["ratio"]
                service[node][subnode]["bandwidth"] = edge_bw
                service.node[subnode]["bandwidth"] = service.node[subnode]["bandwidth"] + edge_bw


def get_nodes_by_type(type, graph):
    '''

    :param type: "VHG"
    :param graph:
    :return: ["VHG1","VHG2"]
    '''
    return [n[0] for n in graph.nodes(data=True) if n[1].get("type") == type]


def get_all_possible_edge_for_2_lists(left, right):
    res = [[]]
    for l in left:
        rres = []
        for r in right:
            for elt in res:
                elt_copy = copy.copy(elt)
                elt_copy.append((l, r))
                rres.append(elt_copy)

        res = rres

    # remove cases where a server is not used, if possible.
    if len(left) >= len(right):
        res = [o for o in res if len(set([x for t in o for x in t])) == len(left) + len(right)]
    return res


def get_all_possible_edges(thelist):
    '''

    :param thelist: a list of list of items (layers)
    :return: a list containing every possible list taling layers into account
    '''
    l = thelist.pop(0)
    r = thelist.pop(0)
    res = [[]]
    while True:
        rres = []
        new = get_all_possible_edge_for_2_lists(l, r)

        for elt in res:
            for new_elt in new:
                elt_copy = copy.copy(elt)
                elt_copy += (new_elt)
                rres.append(elt_copy)
        res = rres
        if len(thelist) != 0:
            l = r
            r = thelist.pop(0)
        else:
            break
    return res


# this class build a full service topology
class ServiceTopoFull(AbstractServiceTopo):
    def __init__(self, sla, vhg_count, vcdn_count, hint_node_mappings=None):
        super(ServiceTopoFull, self).__init__(sla, vhg_count, vcdn_count, hint_node_mappings)

    def compute_service_topo(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay,
                             hint_node_mappings=None):
        vhg_count = min(len(mapped_start_nodes), vhg_count)
        vcdn_count = min(vcdn_count, vhg_count)

        service = nx.DiGraph()


        for i in range(1, vhg_count + 1):
            service.add_node("VHG%d" % i, type="VHG")

        for i in range(1, vcdn_count + 1):
            service.add_node("VCDN%d" % i, type="VCDN", cpu=0, delay=delay, ratio=0)

        for index, cdn in enumerate(mapped_cdn_nodes, start=1):
            service.add_node("CDN%d" % index, type="CDN", cpu=0, ratio=0)

        for key, slaNodeSpec in enumerate(mapped_start_nodes, start=1):
            service.add_node("S%d" % key, cpu=0, type="S", mapping=slaNodeSpec.topoNode.name,
                             bandwidth=slaNodeSpec.attributes["bandwidth"])

            for i in range(1, vhg_count + 1):
                service.add_edge("S%d" % key, "VHG%d" % i)

        for vhg in range(1, vhg_count + 1):
            for vcdn in range(1, vcdn_count + 1):
                service.add_edge("VHG%d" % vhg, "VCDN%d" % vcdn)
            for index, cdn in enumerate(mapped_cdn_nodes, start=1):
                service.add_edge("VHG%d" % vhg, "CDN%d" % index)

        return service, [], {}
