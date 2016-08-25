import sys

import networkx as nx
from networkx.algorithms.components.connected import node_connected_component

from offline.core.combinatorial import get_node_clusters


class ServiceTopo:
    def __init__(self, sla, vhg_count, vcdn_count):
        self.sla = sla
        self.servicetopo = self.__compute_service_topo(sla, vhg_count, vcdn_count)

    def __compute_service_topo(self, sla, vhg_count, vcdn_count):
        service = nx.DiGraph(sla=sla)
        service.add_node("S0", cpu=0)

        for i in range(1, vhg_count + 1):
            service.add_node("VHG%d" % i, type="VHG", cpu=1)

        for i in range(1, vcdn_count + 1):
            service.add_node("vCDN%d" % i, type="VCDN", cpu=5)

        for index, cdn in enumerate(sla.get_cdn_nodes(), start=1):
            service.add_node("CDN%d" % index, type="CDN", cpu=0)

        for key, topoNode in enumerate(sla.get_start_nodes(), start=1):
            service.add_node("S%d" % key, cpu=0, type="S", mapping=topoNode.toponode_id)
            service.add_edge("S0", "S%d" % key, delay=sys.maxint, bandwidth=0)

        for toponode_id, vmg_id in get_node_clusters(map(lambda x: x.toponode_id, sla.get_start_nodes()), vhg_count,
                                                     substrate=sla.substrate).items():
            service.add_edge("S%d" % vmg_id, "VHG%d" % vmg_id,delay=sys.maxint, bandwidth=0)

        service.node["S0"]["bandwidth"] = 1 #sla.bandwidth


        workin_nodes = ["S0"]
        while len(workin_nodes) > 0:
            node = workin_nodes.pop()
            bandwidth = service.node[node].get("bandwidth", 0.0)
            children = service[node].items()
            for subnode, data in children:
                workin_nodes.append(subnode)
                edge_bw = bandwidth / float(len(children))
                service[node][subnode]["bandwidth"]=edge_bw
                service.node[subnode]["bandwidth"] = service.node[subnode].get("bandwidth", 0.0) + edge_bw

        return service

    def dump_nodes(self):
        '''
        :return: a list of tuples containing nodes and their properties
        '''
        res = []
        for node in node_connected_component(self.servicetopo.to_undirected(), "S0"):
            res.append((node + "_%d" % self.sla.id, self.servicetopo.node[node]["cpu"]))
        return res

    def dump_edges(self):
        '''
        :return: a list of tuples containing nodes and their properties
        '''
        res = []
        for start, ends in self.servicetopo.edge.items():
            for end in ends:
                edge = self.servicetopo[start][end]
                res.append((start + "_%d" % self.sla.id, end + "_%d" % self.sla.id, edge["delay"], edge["bandwidth"]))
        return res
