import os
import re
import subprocess
import time

import networkx as nx
from jinja2 import Environment, PackageLoader
from sqlalchemy.orm.exc import NoResultFound

from ..core.mapping import Mapping
from ..time.persistence import NodeMapping, EdgeMapping

OPTIM_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../optim')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')
PRICING_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../pricing')

env = Environment(loader=PackageLoader("offline", 'optim'))
template_optim = env.get_template('optim.zpl.tpl')
# template_optim_slow = env.get_template('optim-slow.zpl.tpl')
template_optim_debug = env.get_template('batch-debug.sh')


def get_node_mapping(node, service, snode_id):
    service_node = next(x for x in service.serviceNodes if x.name == snode_id)
    node_mapping = NodeMapping(node=node, service_node=service_node, service=service)
    return node_mapping


def get_edge_mapping(node_1, node_2, service, snode_1, snode_2):
    node_1 = next(x for x in service.sla.substrate.nodes if x.name == node_1)
    node_2 = next(x for x in service.sla.substrate.nodes if x.name == node_2)
    edge = next(
        x for x in service.sla.substrate.edges if (x.node_1 == node_1 and x.node_2 == node_2) or (
            x.node_1 == node_2 and x.node_2 == node_1))
    snode_1 = next(x for x in service.serviceNodes if x.name == snode_1)
    snode_2 = next(x for x in service.serviceNodes if x.name == snode_2)
    sedge = next(
        x for x in service.serviceEdges if x.node_1_id == snode_1.id and x.node_2_id == snode_2.id)
    edge_mapping = EdgeMapping(edge=edge, serviceEdge=sedge)
    return edge_mapping


def save_node_mapping(substrate, service, nodes_sols, snode, node):
    node = next(x for x in substrate.nodes if x.name == node)
    service_node = next(x for x in service.serviceNodes if x.name == snode)
    node_mapping = NodeMapping(node=node, service_node=service_node, service=service)
    nodes_sols.append(node_mapping)


class DummySolver(object):
    def __init__(self, rs):
        self.rs = rs

    def solve(self, service, substrate):

        service_graph = service.service_graph

        starters = service_graph.get_starters_data()

        nodes_sols = []
        edges_sol = []

        # write the mapping for pre-mapped nodes
        for sname, snode_name, _ in starters :
            node = next(x for x in substrate.nodes if x.name == snode_name)
            service_node = next(x for x in service.serviceNodes if x.name == sname)
            node_mapping = NodeMapping(node=node, service_node=service_node, service=service)
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
                # pick random node
                if service_graph.get_substrate_mapping(snode_name) is None:
                    random_mapped_node = self.rs.choice(avail_node_with_enough_cpu, replace=False)
                else:
                    tnode_name = service_graph.get_substrate_mapping(snode_name)
                    random_mapped_node = next((node for node in substrate.nodes if node.name == tnode_name))

                # print("random mapped node: %s" % random_mapped_node )
                result_bag.append(get_node_mapping(random_mapped_node, service, snode_name))
                # for each service node on the left of this one, supposedly mapped
                for snode1, snode2, sedge_attr in service_graph.get_left_edges(snode_name):
                    # remove topo edge that can handle service bw demand
                    bw = sedge_attr["bandwidth"]
                    constraints_sub = substrate.get_nxgraph().copy()
                    for topo_node1, topo_node2, topo_attr in substrate.get_nxgraph().edges(data=True):
                        if topo_attr["bandwidth"] < bw:
                            constraints_sub.remove_edge(topo_node1, topo_node2)

                    # compute the shortest path between the two nodes (mapped, and random)
                    steps = nx.shortest_path(constraints_sub, random_mapped_node.name,
                                             service_graph.get_substrate_mapping(snode1))
                    # add each topo edge belonging to the shortest path to the mapping
                    for tnode_to_add_to_mapping1, tnode_to_add_to_mapping2 in list(zip(steps, steps[1:])):
                        em = get_edge_mapping(tnode_to_add_to_mapping1, tnode_to_add_to_mapping2, service, snode1,
                                              snode2)
                        # print(em)
                        result_bag.append(em)
                        # print(em)
                    mapped = True
            # update mapping info in service_graph
            for node_mapping in filter(lambda x: isinstance(x, NodeMapping), result_bag):
                service_graph.nx_service_graph.node[node_mapping.service_node.name]["mapping"] = node_mapping.node.name
                nodes_sols.append(node_mapping)

            edges_sol += filter(lambda x: isinstance(x, EdgeMapping), result_bag)

        mapping = Mapping(node_mappings=nodes_sols, edge_mappings=edges_sol, objective_function=0)
        mapping.update_objective_function()

        if mapping is not None:
            service.mapping = mapping
            mapping.substrate = substrate
            mapping.service = service

        return mapping


class ILPSolver(object):
    @classmethod
    def __solve_ILP(cls, service, path):
        '''
        solve without rewriting intermedia files
        :return: a mapping
        '''

        if not os.path.exists(os.path.join(RESULTS_FOLDER, path)):
            os.makedirs(os.path.join(RESULTS_FOLDER, path))

        # copy template to target folder
        with open(os.path.join(RESULTS_FOLDER, path, "optim.zpl"), "w") as f:
            f.write(template_optim.render(dir=os.path.join(RESULTS_FOLDER, path), pricing_dir=PRICING_FOLDER))

        # debug script
        with open(os.path.join(RESULTS_FOLDER, path, "debug.sh"), "w") as f:
            f.write(template_optim_debug.render(dir=os.path.join(RESULTS_FOLDER, path), pricing_dir=PRICING_FOLDER))

        os.chmod(os.path.join(RESULTS_FOLDER, path, "debug.sh"), 0o711)

        # with open(os.path.join(RESULTS_FOLDER, path, "debug.sh"), "w") as f:
        #    f.write(template_optim_debug.render(dir=os.path.join(RESULTS_FOLDER, path), pricing_dir=PRICING_FOLDER))
        # os.chmod(os.path.join(RESULTS_FOLDER, path, "debug.sh"), 0o711)
        subprocess.call(["scip", "-c", "read %s" % os.path.join(RESULTS_FOLDER, path, "optim.zpl"), "-c",
                         "read %s" % os.path.join(RESULTS_FOLDER, path, "solutions.data sol"), "-c",
                         "set reoptimization enable true", "-c", "optimize ", "-c",
                         "write solution %s" % (os.path.join(RESULTS_FOLDER, path, "solutions.data")), "-c",
                         "q"],
                        stdout=open(os.devnull, 'wb')
                        )

        # plotting.plotsol()
        # os.subprocess.call(["cat", "./substrate.dot", "|", "dot", "-Tpdf", "-osol.pdf"])
        with open(os.path.join(RESULTS_FOLDER, path, "solutions.data"), "r") as sol:
            data = sol.read()
            if "infeasible" in data or "no solution" in data:
                return None

            data = data.split("\n")
            nodes_sols = []
            edges_sol = []
            objective_function = None
            for line in data:

                # search node
                matches = re.findall("^x\$(.*)\$([^ \t]+) +([^ \t]+)", line)
                if (len(matches) > 0):
                    try:
                        node = next(x for x in service.sla.substrate.nodes if x.name == matches[0][0])
                        snode_id = matches[0][1]
                        nodes_sols.append(get_node_mapping(node, service, snode_id))
                        continue
                    except NoResultFound as e:
                        print(e)

                # search edge
                matches = re.findall("^y\$(.*)\$(.*)\$(.*)\$([^ \t]+) +([^ \t]+)", line)
                if (len(matches) > 0):
                    node_1, node_2, snode_1, snode_2, value = matches[0]
                    edges_sol.append(get_edge_mapping(node_1, node_2, service, snode_1, snode_2))
                    continue

                matches = re.findall("^objective value: *([0-9\.]*)$", line)
                if len(matches) > 0:
                    objective_function = float(matches[0])
                    continue
        mapping = Mapping(node_mappings=nodes_sols, edge_mappings=edges_sol, objective_function=objective_function)
        return mapping

    @classmethod
    def cleanup(cls):
        for f in [os.path.join(RESULTS_FOLDER, "service.edges.data"),
                  os.path.join(RESULTS_FOLDER, "service.path.data"),
                  os.path.join(RESULTS_FOLDER, "service.path.delay.data"),
                  os.path.join(RESULTS_FOLDER, "service.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "CDN.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "starters.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "cdnmax.data"),
                  os.path.join(RESULTS_FOLDER, "VHG.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "VCDN.nodes.data")]:
            if os.path.isfile(f):
                os.remove(f)

    @classmethod
    def write_substrate_topology(cls, substrate, path):
        assert path != "."

        if not os.path.exists(os.path.join(RESULTS_FOLDER, path)):
            os.makedirs(os.path.join(RESULTS_FOLDER, path))

        edges_file = os.path.join(RESULTS_FOLDER, path, "substrate.edges.data")
        nodes_file = os.path.join(RESULTS_FOLDER, path, "substrate.nodes.data")
        with open(edges_file, 'w') as f:
            for edge in sorted(substrate.edges, key=lambda x: x.node_1.name):
                f.write("%s\n" % edge)

        with open(nodes_file, 'w') as f:
            for node in sorted(substrate.nodes, key=lambda x: x.name):
                f.write("%s\n" % node)

    @classmethod
    def write_service_topology(cls, service_graph, path):
        if not os.path.exists(os.path.join(RESULTS_FOLDER, path)):
            os.makedirs(os.path.join(RESULTS_FOLDER, path))

        mode = "w"

        # write info on the edge
        with open(os.path.join(RESULTS_FOLDER, path, "service.edges.data"), mode) as f:
            for start, end, bw in service_graph.dump_edges():
                f.write("%s\t\t%s\t\t%lf\n" % (start.ljust(20), end, bw))

        with open(os.path.join(RESULTS_FOLDER, path, "service.nodes.data"), mode) as f:
            for snode_id, cpu, bw in service_graph.get_service_nodes():
                f.write("%s\t\t%lf\t\t%lf\n" % (str(snode_id).ljust(20), cpu, bw))

                # write constraints on CDN placement
        with open(os.path.join(RESULTS_FOLDER, path, "CDN.nodes.data"), mode) as f:
            for node, mapping, bw in service_graph.get_CDN_data():
                f.write("%s %s\n" % (node, mapping))

        # write constraints on starter placement
        with open(os.path.join(RESULTS_FOLDER, path, "starters.nodes.data"), mode) as f:
            for s, mapping, bw in service_graph.get_starters_data():
                f.write("%s %s %lf\n" % (s, mapping, bw))

        # write the names of the VHG Nodes
        with open(os.path.join(RESULTS_FOLDER, path, "VHG.nodes.data"), mode) as f:
            for vhg in service_graph.get_vhg():
                f.write("%s\n" % vhg)

        # write the names of the VCDN nodes
        with open(os.path.join(RESULTS_FOLDER, path, "VCDN.nodes.data"), mode) as f:
            for vcdn in service_graph.get_vcdn():
                f.write("%s\n" % (vcdn))

                # write path to associate e2e delay

        with open(os.path.join(RESULTS_FOLDER, path, "service.path.delay.data"), "w") as f:

            for apath, delay in service_graph.dump_delay_paths():
                f.write("%s %lf\n" % (apath, delay))

        # write e2e delay constraint
        with open(os.path.join(RESULTS_FOLDER, path, "service.path.data"), "w") as f:

            for apath, s1, s2 in service_graph.dump_delay_routes():
                f.write("%s %s %s\n" % (apath, s1, s2))

    def solve(self, service, substrate):
        '''
        try to map the provided service on the substrate
        :param service:
        :param substrate:
        :return: a mapping or None in case of Failure
        '''
        path = os.path.join("ILP", str(int(round(time.time() * 1000))))

        ILPSolver.write_substrate_topology(substrate, path=path)
        ILPSolver.write_service_topology(service.service_graph, path=path)
        mapping = self.__solve_ILP(service, path=path)

        if mapping is not None:
            mapping.update_objective_function()
            service.mapping = mapping
            mapping.substrate = substrate
            mapping.service = service

        return mapping
