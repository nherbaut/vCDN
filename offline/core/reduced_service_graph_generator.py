import collections
import operator
import sys
import traceback

import networkx as nx
from networkx import shortest_path

from offline.core.combinatorial import get_node_clusters, get_vhg_cdn_mapping
from offline.core.ilpsolver import ILPSolver
from offline.core.service_graph import ServiceGraph
from offline.core.service_graph_generator import AbstractServiceGraphGenerator, get_nodes_by_type
from offline.pricing.generator import get_vmg_calculator, get_vcdn_calculator


class ComposedServiceGraphGenerator(AbstractServiceGraphGenerator):
    def __init__(self, sla, klass):
        self.sla = sla
        self.klass = klass

    def get_service_topologies(self):
        for vhg in range(1, len(self.sla.get_start_nodes()) + 1):
            for vcdn in range(1, vhg + 1):
                for topo in self.klass(sla=self.sla, vhg_count=vhg, vcdn_count=vcdn).get_service_topologies():
                    yield topo


class HeuristicServiceGraphGenerator(AbstractServiceGraphGenerator):
    def __init__(self, sla, vhg_count=None, vcdn_count=None, solver=None):
        super(HeuristicServiceGraphGenerator, self).__init__(sla, vhg_count, vcdn_count)
        if solver is not None:
            self.solver = solver()
        else:
            self.solver = ILPSolver()

    def compute_service_topos(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay):

        service_graphs_partial = self.__compute_service_topos(substrate, mapped_start_nodes, mapped_cdn_nodes,
                                                              vhg_count,
                                                              vcdn_count, delay,
                                                              None)

        for service_graph_partial in service_graphs_partial:
            from offline.core.service import Service
            dummy_service = Service(service_graph_partial, self.sla, self.solver)
            mapping = self.solver.solve(service=dummy_service, substrate=substrate)
            if mapping is not None:
                yield self.__compute_service_topos(substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count,
                                                   vcdn_count, delay, mapping.node_mappings)

    def __compute_service_topos(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay,
                                hint_node_mappings=None):
        '''

        :param substrate:
        :param mapped_start_nodes:
        :param mapped_cdn_nodes:
        :param vhg_count:
        :param vcdn_count:
        :param delay:
        :param hint_node_mappings:
        :return: a service_graph ServiceGraph that contains the service to embed
        '''
        if vhg_count is None:
            vhg_count = len(mapped_start_nodes)
        else:
            vhg_count = min(len(mapped_start_nodes), vhg_count)

        if vcdn_count is None:
            vcdn_count = vhg_count
        else:
            vcdn_count = min(vcdn_count, vhg_count)

        vmg_calc = get_vmg_calculator()
        vcdn_calc = get_vcdn_calculator()
        nx_service_graph = nx.DiGraph()

        for i in range(1, vhg_count + 1):
            nx_service_graph.add_node("VHG%d" % i, type="VHG", ratio=1, bandwidth=0)

        for i in range(1, vcdn_count + 1):
            nx_service_graph.add_node("VCDN%d" % i, type="VCDN", cpu=0, delay=delay, ratio=0.35, bandwidth=0)

        for key, slaNodeSpec in enumerate(mapped_start_nodes, start=1):
            nx_service_graph.add_node("S%d" % key, cpu=0, type="S", mapping=slaNodeSpec.topoNode.name, bandwidth=0)

        # create s<-> vhg edges
        score, cluster = get_node_clusters([x.topoNode.name for x in mapped_start_nodes], vhg_count,
                                           substrate=substrate)
        for toponode_name, vmg_id in list(cluster.items()):
            s = [n[0] for n in nx_service_graph.nodes(data=True) if n[1].get("mapping", None) == toponode_name][0]
            nx_service_graph.add_edge(s, "VHG%d" % vmg_id, delay=sys.maxsize, bandwidth=0)

        # create vhg <-> vcdn edges
        # here, each S "votes" for a TE and tell its VHG

        score, cluster = get_node_clusters([x.topoNode.name for x in mapped_start_nodes], vcdn_count,
                                           substrate=substrate)
        for toponode_name, vCDN_id in list(cluster.items()):
            # get the S from the toponode_id
            s = [n[0] for n in nx_service_graph.nodes(data=True) if n[1].get("mapping", None) == toponode_name][0]

            vcdn = "VCDN%d" % vCDN_id
            # get the vhg from the S
            vhg = list(nx_service_graph[s].items())[0][0]

            # apply the votes
            if "votes" not in nx_service_graph.node[vhg]:
                nx_service_graph.node[vhg]["votes"] = collections.defaultdict(lambda: {})
                nx_service_graph.node[vhg]["votes"][vcdn] = 1
            else:
                nx_service_graph.node[vhg]["votes"][vcdn] = nx_service_graph.node[vhg]["votes"].get(vcdn, 0) + 1

        # create the edge according to the votes
        for vhg in [n[0] for n in nx_service_graph.nodes(data=True) if n[1].get("type") == "VHG"]:
            votes = nx_service_graph.node[vhg]["votes"]
            winners = max(iter(list(votes.items())), key=operator.itemgetter(1))
            if len(winners) == 1:
                nx_service_graph.add_edge(vhg, winners[0], bandwidth=0)
            else:
                nx_service_graph.add_edge(vhg, winners[0], bandwidth=0)

        # delay path
        delay_path = {}
        delay_route = collections.defaultdict(lambda: [])
        for vcdn in get_nodes_by_type("VCDN", nx_service_graph):
            for s in get_nodes_by_type("S", nx_service_graph):
                try:
                    sp = shortest_path(nx_service_graph, s, vcdn)
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
                for vhg, cdn in list(get_vhg_cdn_mapping(vhg_mapping, cdn_mapping, substrate).items()):
                    if vhg in nx_service_graph.node:
                        nx_service_graph.add_edge(vhg, cdn, bandwidth=0, price_factor=0)

                for index, cdn in enumerate(mapped_cdn_nodes, start=1):
                    if "CDN%d" % index in nx_service_graph.nodes():
                        nx_service_graph.add_node("CDN%d" % index, type="CDN", cpu=0, ratio=0.65, name="CDN%d" % index,
                                                  bandwidth=0,
                                                  mapping=cdn.topoNode.name)

        except:
            traceback.print_exc()
            exit(-1)

        self.propagate_bandwidth(nx_service_graph, mapped_start_nodes)

        # assign CPU according to Bandwidth
        for vhg in get_nodes_by_type("VHG", nx_service_graph):
            nx_service_graph.node[vhg]["cpu"] = vmg_calc(nx_service_graph.node[vhg]["bandwidth"])

        for vhg in get_nodes_by_type("VCDN", nx_service_graph):
            nx_service_graph.node[vhg]["cpu"] = vcdn_calc(nx_service_graph.node[vhg]["bandwidth"])

        yield ServiceGraph(nx_service_graph, delay_path, delay_route, delay)
