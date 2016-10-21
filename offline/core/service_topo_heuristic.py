import collections
import operator
import sys
import traceback

import networkx as nx
from networkx import shortest_path

from offline.core.combinatorial import get_node_clusters, get_vhg_cdn_mapping
from offline.core.service_topo import AbstractServiceTopo, get_nodes_by_type
from offline.core.topo_instance import TopoInstance
from offline.pricing.generator import get_vmg_calculator, get_vcdn_calculator


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

        for i in range(1, vhg_count + 1):
            service.add_node("VHG%d" % i, type="VHG", ratio=1, bandwidth=0)

        for i in range(1, vcdn_count + 1):
            service.add_node("VCDN%d" % i, type="VCDN", cpu=0, delay=delay, ratio=0.35, bandwidth=0)


        for index, cdn in enumerate(mapped_cdn_nodes, start=1):
            service.add_node("CDN%d" % index, type="CDN", cpu=0, ratio=0.65, name="CDN%d" % index, bandwidth=0,
                                   mapping=cdn.topoNode.name)

        for key, slaNodeSpec in enumerate(mapped_start_nodes, start=1):
            service.add_node("S%d" % key, cpu=0, type="S", mapping=slaNodeSpec.topoNode.name, bandwidth=0)

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
                for vhg, cdn in get_vhg_cdn_mapping(vhg_mapping, cdn_mapping,substrate).items():
                    if vhg in service.node:
                        service.add_edge(vhg, cdn, bandwidth=0,)

        except:
            traceback.print_exc()
            exit(-1)

        self.propagate_bandwidth(service, mapped_start_nodes)

        # assign CPU according to Bandwidth
        for vhg in get_nodes_by_type("VHG", service):
            service.node[vhg]["cpu"] = vmg_calc(service.node[vhg]["bandwidth"])

        for vhg in get_nodes_by_type("VCDN", service):
            service.node[vhg]["cpu"] = vcdn_calc(service.node[vhg]["bandwidth"])


        ti = TopoInstance(service, delay_path, delay_route, delay)
        yield ti
