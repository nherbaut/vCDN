import copy

import networkx as nx


class AbstractServiceTopo(object):
    def __init__(self, sla, vhg_count, vcdn_count, hint_node_mappings=None):
        mapped_start_nodes = sla.get_start_nodes()
        mapped_cdn_nodes = sla.get_cdn_nodes()
        self.sla_id = sla.id
        self.topoinfos = self.compute_service_topo(
            mapped_start_nodes=mapped_start_nodes, mapped_cdn_nodes=mapped_cdn_nodes, vhg_count=vhg_count,
            vcdn_count=vcdn_count, delay=sla.delay,
            hint_node_mappings=hint_node_mappings, substrate=sla.substrate, )


    def getTopos(self):
        return self.topoinfos

    def propagate_bandwidth(self, service, mapped_start_nodes):
        # assign bandwidth
        workin_nodes = []
        for index, sla_node_spec in enumerate(mapped_start_nodes, start=1):
            service.node["S%d" % index]["bandwidth"] = sla_node_spec.attributes["bandwidth"]
            workin_nodes.append("S%d" % index)

        while len(workin_nodes) > 0:
            node = workin_nodes.pop(0)
            bandwidth = service.node[node].get("bandwidth", 0.0)
            children = service[node].items()
            for subnode, data in children:
                if subnode not in workin_nodes:
                    workin_nodes.append(subnode)
                edge_bw = bandwidth * service.node[subnode]["ratio"]
                service[node][subnode]["bandwidth"] = edge_bw
                service.node[subnode]["bandwidth"] = service.node[subnode]["bandwidth"] + edge_bw
                #print "\n\n"+"\n".join([str(n[0])+"->"+str(n[1]["bandwidth"]) for n in sorted(service.nodes(data=True),key=lambda x:x[0])])


def get_nodes_by_type(type, graph):
    '''

    :param type: "VHG"
    :param graph:
    :return: ["VHG1","VHG2"]
    '''
    return sorted([n[0] for n in graph.nodes(data=True) if n[1].get("type") == type])


def get_all_possible_edge_for_2_lists(left, right, all_rights_are_mandatory=True):
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
    if all_rights_are_mandatory and (len(left) >= len(right)):
        res = [o for o in res if len(set([x for t in o for x in t])) == len(left) + len(right)]
    return res


def get_all_possible_edges(thelist, all_rights_are_mandatory=True):
    '''

    :param thelist: a list of list of items (layers)
    :return: a list containing every possible list taling layers into account
    '''
    l = thelist.pop(0)
    r = thelist.pop(0)
    res = [[]]
    while True:
        rres = []
        new = get_all_possible_edge_for_2_lists(l, r, all_rights_are_mandatory)

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



