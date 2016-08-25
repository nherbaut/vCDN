import collections
import operator
import sys
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms.components.connected import node_connected_component
from networkx.algorithms.shortest_paths.generic import shortest_path

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
            service.add_node("vCDN%d" % i, type="VCDN", cpu=5, delay=sla.delay)

        for index, cdn in enumerate(sla.get_cdn_nodes(), start=1):
            service.add_node("CDN%d" % index, type="CDN", cpu=0)

        for key, topoNode in enumerate(sla.get_start_nodes(), start=1):
            service.add_node("S%d" % key, cpu=0, type="S", mapping=topoNode.toponode_id)
            service.add_edge("S0", "S%d" % key, delay=sys.maxint, bandwidth=0)

        # create s<-> vhg edges
        for toponode_id, vmg_id in get_node_clusters(map(lambda x: x.toponode_id, sla.get_start_nodes()), vhg_count,
                                                     substrate=sla.substrate).items():
            s = [n[0] for n in service.nodes(data=True) if n[1].get("mapping", None) == toponode_id][0]
            service.add_edge(s, "VHG%d" % vmg_id, delay=sys.maxint, bandwidth=0)

        # create vhg <-> vcdn edges
        # here, each S "votes" for a vCDN and tell its VHG

        for toponode_id, vCDN_id in get_node_clusters(map(lambda x: x.toponode_id, sla.get_start_nodes()), vcdn_count,
                                                      substrate=sla.substrate).items():
            # get the S from the toponode_id
            s = [n[0] for n in service.nodes(data=True) if n[1].get("mapping", None) == toponode_id][0]

            vcdn = "VCDN%d" % vCDN_id
            # get the vhg from the S
            vhg = service[s].items()[0][0]
            print vhg
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
                service.add_edge(vhg, winners[0],bandwidth=0)
            else:
                print("several winners... %s taking the first one" % str(winners))
                service.add_edge(vhg, winners[0],bandwidth=0)

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

        rservice = service.reverse(copy=True)
        sp = shortest_path(rservice, "VCDN1", "S1")

        return service

    def dump_nodes(self):
        '''
        :return: a list of tuples containing nodes and their properties
        '''
        res = []
        for node in node_connected_component(self.servicetopo.to_undirected(), "S0"):
            res.append((node + "_%d" % self.sla.id, self.servicetopo.node[node].get("cpu",0)))
        return res

    def dump_edges(self):
        '''
        :return: a list of tuples containing nodes and their properties
        '''
        res = []
        for start, ends in self.servicetopo.edge.items():
            for end in ends:
                edge = self.servicetopo[start][end]
                res.append((start + "_%d" % self.sla.id, end + "_%d" % self.sla.id, edge["bandwidth"]))
        return res
