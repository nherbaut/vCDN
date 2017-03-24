import networkx as nx

from offline.core.service_graph_generator import get_nodes_by_type


class ServiceGraph:
    '''
    thin wrapper around a nx graph that implement custom service graph features
    '''

    def __init__(self, nx_service_graph, delay_path, delay_routes, delay):
        self.nx_service_graph = nx_service_graph.copy()
        self.delay_paths = delay_path
        self.delay_routes = delay_routes
        self.delay = delay

    def __str__(self):
        return "%s" % self.nx_service_graph.edge

    def compute_service_topo(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay,
                             hint_node_mappings=None):
        raise NotImplementedError("Must override methodB")

    def get_left_nodes(self, node, data=False):
        if not data:
            return set(
                [n for n in self.nx_service_graph.nodes() for item in self.nx_service_graph[n].items() if
                 item[0] == node])
        else:
            return [(n, self.nx_service_graph.node[n]) for n in self.nx_service_graph.nodes() for item in
                    self.nx_service_graph[n].items() if
                    item[0] == node]

    def get_left_edges(self, node):
        for left_node in self.get_left_nodes(node):
            yield left_node, node, self.nx_service_graph[left_node][node]

    def get_substrate_mapping(self, node):
        return self.nx_service_graph.node[node].get("mapping", None)

    def get_type_from_node(self, node):
        return self.nx_service_graph.node[node]["type"]

    @classmethod
    def get_left_type_from_type(cls, atype):
        if atype == "S":
            return None
        elif atype == "VHG":
            return "S"
        elif atype == "CDN":
            return "VHG"
        elif atype == "VCDN":
            return "VHG"
        else:
            return None

    def get_vhg_count(self):
        return len(self.get_vhg())

    def get_vcdn_count(self):
        return len(self.get_vcdn())

    def get_vhg(self, data=False):
        return get_nodes_by_type("VHG", self.nx_service_graph, data)

    def get_vcdn(self, data=False):
        return get_nodes_by_type("VCDN", self.nx_service_graph, data)

    def get_cdn(self, data=False):
        return get_nodes_by_type("CDN", self.nx_service_graph, data)

    def get_starters(self,data=False):
        return get_nodes_by_type("S", self.nx_service_graph,data)

    def set_node_mapping(self, service_node_name, phyisical_node_name):
        self.nx_service_graph.node[service_node_name]["mapping"] = phyisical_node_name

    def get_starters_data(self):
        '''

        :return: a list of tuple with (name, mapping, bandwith)
        '''
        return [(s, self.nx_service_graph.node[s]["mapping"], self.nx_service_graph.node[s]["bandwidth"]) for s in
                get_nodes_by_type("S", self.nx_service_graph)]

    def get_CDN_data(self):
        return [(s, self.nx_service_graph.node[s]["mapping"], self.nx_service_graph.node[s]["bandwidth"]) for s in
                get_nodes_by_type("CDN", self.nx_service_graph)]

    def get_service_nodes(self):
        for node in self.nx_service_graph.nodes(data=True):
            yield node[0], node[1].get("cpu", 0), node[1].get("bandwidth", 0)

    def get_service_cdn_nodes(self):
        cdns = self.get_cdn()
        for node in self.nx_service_graph.nodes(data=True):
            if node[0] in cdns:
                yield node[0], node[1].get("cpu", 0)

    def get_closest_node(self, n1, targets, weight=None):
        return \
            min([(target, nx.shortest_path_length(self.nx_service_graph, n1, target, weight=weight)) for target in
                 targets],
                key=lambda x: x[1])[0]

    def get_max_bw_between_nodes(self, n1, n2):
        if n1 == n2:
            return 0
        elif n2 in self.nx_service_graph[n1]:
            return self.nx_service_graph[n1][n2]["bandwidth"]
        elif n1 in self.nx_service_graph[n2]:
            return self.nx_service_graph[n2][n1]["bandwidth"]
        else:
            path_nodes = nx.shortest_path(self.nx_service_graph, n1, n2)
            return max([self.get_max_bw_between_nodes(segment[0], segment[1]) for segment in
                        list(zip(path_nodes, path_nodes[1:]))])

    def dump_edges(self):
        '''
        :return: [(start , end , bandwidth)]
        '''
        res = []
        for start, ends in list(self.nx_service_graph.edge.items()):
            for end in ends:
                edge = self.nx_service_graph[start][end]
                res.append((start, end, edge.get("bandwidth", 0)))
        return res

    def get_service_CDN_edges(self):
        '''

        :return: start, end, edge["bandwidth"]
        '''
        for start, ends in list(self.nx_service_graph.edge.items()):
            cdns = self.get_cdn()
            for end in [end for end in ends if end in cdns]:
                edge = self.nx_service_graph[start][end]
                yield start, end, edge.get("bandwidth", 0)

    def get_service_edges(self):
        '''

        :return: start, end, edge["bandwidth"]
        '''
        for start, ends in list(self.nx_service_graph.edge.items()):
            for end in ends:
                edge = self.nx_service_graph[start][end]
                yield start, end, edge.get("bandwidth", 0)

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
        for path, segments in list(self.delay_routes.items()):
            for segment in segments:
                res.append((path, segment[0], segment[1]))

        return res

    def dump_delay_edge_dict(self):
        '''
        for each edge on the service graph, gives a delay such that the e2e delay can be achieved
        :return: {(sn1,sn2):delay}
        '''
        res = dict()
        for path2, delay in self.dump_delay_paths():
            hops = [(sn1, sn2) for path, sn1, sn2 in self.dump_delay_routes() if path == path2]
            for sn11, sn22 in hops:
                res[(sn11, sn22)] = min(delay / len(hops), res.get((sn11, sn22), 999999))

        return res
