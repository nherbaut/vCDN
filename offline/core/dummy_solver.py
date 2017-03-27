import copy

import networkx as nx

from offline.core.ilpsolver import generate_node_mapping, generate_edge_mapping
from offline.core.mapping import Mapping
from offline.time.persistence import NodeMapping, EdgeMapping


class DummySolver(object):
    def __init__(self, rs, additional_node_mapping={}):
        self.rs = rs
        self.additional_node_mapping = additional_node_mapping

    def solve(self, service, substrate):

        service_graph = service.service_graph
        starters = service_graph.get_starter_triple()
        substrate_graph = substrate.get_nxgraph()
        additional_node_mapping = copy.copy(self.additional_node_mapping)

        for snode, tnode, _ in service_graph.get_cdn_triple():
            additional_node_mapping[snode] = tnode

        nodes_sols = []
        edges_sol = []
        # addinv mapping we already know about, like mapped nodes and provided mapping
        computed_mapping = {x[0]: x[1]["mapping"] for x in
                            (service_graph.get_starters(data=True) + service_graph.get_cdn(data=True))}
        for k, v in self.additional_node_mapping.items():
            computed_mapping[k] = v

            # write the mapping for pre-mapped nodes
        for sname, snode_name, _ in starters:
            node = next(x for x in substrate.nodes if x.name == snode_name)
            service_node = next(x for x in service.serviceNodes if x.name == sname)
            node_mapping = NodeMapping(node=node, service_node=service_node)
            nodes_sols.append(node_mapping)

        avail_nodes = substrate.nodes
        # for each unmapped node
        for snode_name, snode_attr in [(snode_name, snode_attr) for snode_name, snode_attr in
                                       (service_graph.get_vhg(data=True) + service_graph.get_vcdn(
                                           data=True) + service_graph.get_cdn(data=True))]:
            mapped = False
            avail_node_with_enough_cpu = sorted(list(filter(lambda x: x.cpu_capacity > snode_attr["cpu"], avail_nodes)),
                                                key=lambda x: x.name)

            # while it's not mapped
            while mapped is not True:
                result_bag = []
                # if service graph does not already contain mapping (unmapped nodes for examples)
                if computed_mapping.get(snode_name, None) is None:
                    # print("mapping for %s is NOT already known" % snode_name)
                    random_mapped_node = self.rs.choice(avail_node_with_enough_cpu, replace=False)
                else:
                    # print("mapping for %s is already known" % snode_name)
                    tnode_name = computed_mapping.get(snode_name, None)
                    random_mapped_node = next((node for node in substrate.nodes if node.name == tnode_name))

                # print("random mapped node: %s" % random_mapped_node )
                result_bag.append(generate_node_mapping(random_mapped_node, service, snode_name))
                # for each service node on the left of this one, supposedly mapped
                for snode1, snode2, sedge_attr in service_graph.get_left_edges(snode_name):
                    # remove topo edge that can handle service bw demand
                    bw = sedge_attr["bandwidth"]
                    constraints_sub = substrate_graph.copy()
                    for topo_node1, topo_node2, topo_attr in substrate_graph.edges(data=True):
                        if topo_attr["bandwidth"] < bw:
                            constraints_sub.remove_edge(topo_node1, topo_node2)

                    # compute the shortest path between the two nodes (mapped, and random)
                    steps = nx.shortest_path(constraints_sub, random_mapped_node.name,
                                             computed_mapping.get(snode1, None))
                    # add each topo edge belonging to the shortest path to the mapping
                    for tnode_to_add_to_mapping1, tnode_to_add_to_mapping2 in list(zip(steps, steps[1:])):
                        em = generate_edge_mapping(tnode_to_add_to_mapping1, tnode_to_add_to_mapping2, service, snode1,
                                                   snode2)
                        # print(em)
                        result_bag.append(em)
                        # print(em)
                    mapped = True

            # update mapping info in service_graph
            for node_mapping in filter(lambda x: isinstance(x, NodeMapping), result_bag):
                computed_mapping[node_mapping.service_node.name] = node_mapping.node.name
                nodes_sols.append(node_mapping)

            edges_sol += filter(lambda x: isinstance(x, EdgeMapping), result_bag)

        mapping = Mapping(node_mappings=nodes_sols, edge_mappings=edges_sol, objective_function=0)
        mapping.update_objective_function()

        return mapping
