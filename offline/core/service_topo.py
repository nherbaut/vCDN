import collections
import operator
import sys

import networkx as nx
from networkx.algorithms.components.connected import node_connected_component
from networkx.algorithms.shortest_paths.generic import shortest_path

from ..core.combinatorial import get_node_clusters, get_vhg_cdn_mapping


class ServiceTopo:
    def __init__(self, sla, vhg_count, vcdn_count, hint_mapping=None):

        mapped_start_nodes = sla.get_start_nodes()
        mapped_cdn_nodes = sla.get_cdn_nodes()
        self.sla_id = sla.id
        self.delay = sla.delay

        self.servicetopo, self.delay_paths, self.delay_routes = self.__compute_service_topo(
            mapped_start_nodes=mapped_start_nodes, mapped_cdn_nodes=mapped_cdn_nodes, vhg_count=vhg_count,
            vcdn_count=vcdn_count,
            hint_mapping=hint_mapping, substrate=sla.substrate)

    def __compute_service_topo(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count,
                               hint_mapping=None):
        service = nx.DiGraph()
        service.add_node("S0", cpu=0)

        for i in range(1, vhg_count + 1):
            service.add_node("VHG%d" % i, type="VHG", cpu=1)

        for i in range(1, vcdn_count + 1):
            service.add_node("VCDN%d" % i, type="VCDN", cpu=5, delay=self.delay)

        for index, cdn in enumerate(mapped_cdn_nodes, start=1):
            service.add_node("CDN%d" % index, type="CDN", cpu=0)

        for key, topoNode in enumerate(mapped_start_nodes, start=1):
            service.add_node("S%d" % key, cpu=0, type="S", mapping=topoNode.toponode_id)
            service.add_edge("S0", "S%d" % key, delay=sys.maxint, bandwidth=0)

        # create s<-> vhg edges
        for toponode_id, vmg_id in get_node_clusters(map(lambda x: x.toponode_id, mapped_start_nodes), vhg_count,
                                                     substrate=substrate).items():
            s = [n[0] for n in service.nodes(data=True) if n[1].get("mapping", None) == toponode_id][0]
            service.add_edge(s, "VHG%d" % vmg_id, delay=sys.maxint, bandwidth=0)

        # create vhg <-> vcdn edges
        # here, each S "votes" for a vCDN and tell its VHG

        for toponode_id, vCDN_id in get_node_clusters(map(lambda x: x.toponode_id, mapped_start_nodes), vcdn_count,
                                                      substrate=substrate).items():
            # get the S from the toponode_id
            s = [n[0] for n in service.nodes(data=True) if n[1].get("mapping", None) == toponode_id][0]

            vcdn = "VCDN%d" % vCDN_id
            # get the vhg from the S
            vhg = service[s].items()[0][0]
            print
            vhg
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
                #print("several winners... %s taking the first one" % str(winners))
                service.add_edge(vhg, winners[0], bandwidth=0)

        service.node["S0"]["bandwidth"] = 1  # sla.bandwidth

        # assign bandwidth
        workin_nodes = ["S0"]
        while len(workin_nodes) > 0:
            node = workin_nodes.pop()
            bandwidth = service.node[node].get("bandwidth", 0.0)
            children = service[node].items()
            for subnode, data in children:
                workin_nodes.append(subnode)
                edge_bw = bandwidth / float(len(children))
                service[node][subnode]["bandwidth"] = edge_bw
                service.node[subnode]["bandwidth"] = service.node[subnode].get("bandwidth", 0.0) + edge_bw

        # create delay path
        delay_path = {}
        delay_route = collections.defaultdict(lambda: [])
        for vcdn in self.__get_nodes_by_type("VCDN", service):
            for s in self.__get_nodes_by_type("S", service):
                try:
                    sp = shortest_path(service, s, vcdn)
                    key = "_".join(sp)
                    delay_path[key] = self.delay
                    for i in range(len(sp) - 1):
                        delay_route[key].append((sp[i], sp[i + 1]))

                except:
                    continue

        # add CDN edges if available
        if hint_mapping is not None:
            vhg_mapping = [(nm.node_id, nm.service_node_id) for nm in hint_mapping.node_mappings if
                           nm.service_node_id in self.__get_nodes_by_type("VHG", service)]
            cdn_mapping = [(nm.toponode_id, "CDN%d" % index) for index, nm in enumerate(mapped_cdn_nodes, start=1)]
            for vhg, cdn in get_vhg_cdn_mapping(vhg_mapping, cdn_mapping).items():
                service.add_edge(vhg, cdn, bandwidth=service.node[vhg]["bandwidth"])

        return service, delay_path, delay_route

    def __get_nodes_by_type(self, type, graph):
        '''

        :param type: "VHG"
        :param graph:
        :return: ["VHG1","VHG2"]
        '''
        return [n[0] for n in graph.nodes(data=True) if n[1].get("type") == type]

    def dump_nodes(self):
        '''
        :return: [("S2",15.12)]
        '''
        res = []
        for node in node_connected_component(self.servicetopo.to_undirected(), "S0"):
            res.append((node, self.servicetopo.node[node].get("cpu", 0)))
        return res

    def getServiceNodes(self):
        for node in self.servicetopo.nodes(data=True):
            yield node[0], node[1].get("bandwidth", 0)

    def dump_edges(self):
        '''
        :return: start , end , edge["bandwidth"]
        '''
        res = []
        for start, ends in self.servicetopo.edge.items():
            for end in ends:
                edge = self.servicetopo[start][end]
                res.append((start , end , edge["bandwidth"]))
        return res

    def getServiceEdges(self):
        '''

        :return: start, end, edge["bandwidth"]
        '''
        for start, ends in self.servicetopo.edge.items():
            for end in ends:
                edge = self.servicetopo[start][end]
                yield start, end, edge["bandwidth"]

    def dump_delay_paths(self):
        '''

        :return: (path, self.delay)
        '''
        res = []
        for path in self.delay_paths:
            res.append((path, self.delay))

        return res

    def dump_delay_routes(self):
        '''

        :param service_id:
        :return: (path,  segment[0], segment[1]
        '''
        res = []
        for path, segments in self.delay_routes.items():
            for segment in segments:
                res.append((path,  segment[0], segment[1]))

        return res
