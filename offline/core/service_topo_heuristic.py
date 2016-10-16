import collections
import operator
import sys
import traceback

import networkx as nx
from networkx import shortest_path

from offline.time.persistence import Session
from offline.core.combinatorial import get_node_clusters, get_vhg_cdn_mapping
from offline.core.service_topo import AbstractServiceTopo, get_nodes_by_type
from offline.pricing.generator import get_vmg_calculator, get_vcdn_calculator
from offline.core.topo_instance import TopoInstance


class ServiceTopoHeuristic(AbstractServiceTopo):
    def __init__(self, sla, vhg_count, vcdn_count, hint_node_mappings=None):
        super(ServiceTopoHeuristic, self).__init__(sla, vhg_count, vcdn_count, hint_node_mappings)

    def compute_service_topo(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay,
                             hint_node_mappings=None):

        vhg_count = min(len(mapped_start_nodes), vhg_count)
        vcdn_count = min(vcdn_count, vhg_count)

        vmg_calc = get_vmg_calculator()
        vcdn_calc = get_vcdn_calculator()
        service = nx.DiGraph()
        service.add_node("S0", cpu=0)

        for i in range(1, vhg_count + 1):
            service.add_node("VHG%d" % i, type="VHG")

        for i in range(1, vcdn_count + 1):
            service.add_node("VCDN%d" % i, type="VCDN", cpu=105, delay=delay, ratio=0.35)

        for index, cdn in enumerate(mapped_cdn_nodes, start=1):
            service.add_node("CDN%d" % index, type="CDN", cpu=0, ratio=0.65)

        for key, slaNodeSpec in enumerate(mapped_start_nodes, start=1):
            service.add_node("S%d" % key, cpu=0, type="S", mapping=slaNodeSpec.topoNode.name)
            service.add_edge("S0", "S%d" % key, delay=sys.maxint, bandwidth=0)

        # create s<-> vhg edges
        for toponode_name, vmg_id in get_node_clusters(map(lambda x: x.topoNode.name, mapped_start_nodes), vhg_count,
                                                       substrate=substrate).items():
            s = [n[0] for n in service.nodes(data=True) if n[1].get("mapping", None) == toponode_name][0]
            service.add_edge(s, "VHG%d" % vmg_id, delay=sys.maxint, bandwidth=0)

        # create vhg <-> vcdn edges
        # here, each S "votes" for a vCDN and tell its VHG

        for toponode_name, vCDN_id in get_node_clusters(map(lambda x: x.topoNode.name, mapped_start_nodes), vcdn_count,
                                                        substrate=substrate).items():
            # get the S from the toponode_id
            s = [n[0] for n in service.nodes(data=True) if n[1].get("mapping", None) == toponode_name][0]

            vcdn = "VCDN%d" % vCDN_id
            # get the vhg from the S
            vhg = service[s].items()[0][0]

            # apply the votes
            if "votes" not in service.node[vhg]:
                service.node[vhg]["votes"] = collections.defaultdict(lambda: {})
                service.node[vhg]["votes"][vcdn] = 1
            else:
                service.node[vhg]["votes"][vcdn] = service.node[vhg]["votes"].get(vcdn, 0) + 1

        # create the edge according to the votes
        for vhg in [n[0] for n in service.nodes(data=True) if n[1].get("type") == "VHG"]:
            votes = service.node[vhg]["votes"]
            winners = max(votes.iteritems(), key=operator.itemgetter(1))
            if len(winners) == 1:
                service.add_edge(vhg, winners[0], bandwidth=0)
            else:
                service.add_edge(vhg, winners[0], bandwidth=0)

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
                edge_bw = bandwidth / float(len(children)) * service.node[subnode].get("ratio", 1.0)
                service[node][subnode]["bandwidth"] = edge_bw
                service.node[subnode]["bandwidth"] = service.node[subnode].get("bandwidth", 0.0) + edge_bw

        # assign CPU according to Bandwidth
        for vhg in get_nodes_by_type("VHG", service):
            service.node[vhg]["cpu"] = vmg_calc(service.node[vhg]["bandwidth"])

        # delay path
        delay_path = {}
        delay_route = collections.defaultdict(lambda: [])
        for vcdn in get_nodes_by_type("VCDN", service):
            for s in get_nodes_by_type("S", service):
                try:
                    sp = shortest_path(service, s, vcdn)
                    key = "_".join(sp)
                    delay_path[key] = delay
                    for i in range(len(sp) - 1):
                        delay_route[key].append((sp[i], sp[i + 1]))

                except:
                    continue

        # add CDN edges if available
        try:
            if hint_node_mappings is not None:
                vhg_mapping = [(nmapping.node.name, nmapping.service_node.name) for nmapping in hint_node_mappings if
                               "VHG" in nmapping.service_node.name]
                cdn_mapping = [(nm.topoNode.name, "CDN%d" % index) for index, nm in
                               enumerate(mapped_cdn_nodes, start=1)]
                for vhg, cdn in get_vhg_cdn_mapping(vhg_mapping, cdn_mapping).items():
                    if vhg in service.node:
                        service.add_edge(vhg, cdn, bandwidth=service.node[vhg]["bandwidth"])

        except:
            traceback.print_exc()
        ti=TopoInstance(service, delay_path, delay_route, delay)
        yield ti
