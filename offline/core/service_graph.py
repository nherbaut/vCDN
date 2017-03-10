from offline.core.service_graph_generator import get_nodes_by_type


class ServiceGraph:
    '''
    thin wrapper around a nx graph that implement custom service graph features
    '''

    def __init__(self, nx_service_graph, delay_path, delay_routes, delay):
        self.nx_service_graph = nx_service_graph
        self.delay_paths = delay_path
        self.delay_routes = delay_routes
        self.delay = delay

    def __str__(self):
        return "%s" % self.nx_service_graph.edge

    def compute_service_topo(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay,
                             hint_node_mappings=None):
        raise NotImplementedError("Must override methodB")

    def get_vhg_count(self):
        return len(self.get_vhg())

    def get_vcdn_count(self):
        return len(self.get_vcdn())

    def get_vhg(self):
        return get_nodes_by_type("VHG", self.nx_service_graph)

    def get_vcdn(self):
        return get_nodes_by_type("VCDN", self.nx_service_graph)

    def get_cdn(self):
        return get_nodes_by_type("CDN", self.nx_service_graph)

    def get_Starters(self):
        return [(s, self.nx_service_graph.node[s]["mapping"], self.nx_service_graph.node[s]["bandwidth"]) for s in
                get_nodes_by_type("S", self.nx_service_graph)]

    def get_CDN(self):
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
            res.append(path)

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
