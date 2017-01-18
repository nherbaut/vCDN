from offline.core.service_topo import get_nodes_by_type


class TopoInstance:
    def __init__(self, service, delay_path, delay_routes, delay):
        self.servicetopo = service
        self.delay_paths = delay_path
        self.delay_routes = delay_routes
        self.delay = delay

    def compute_service_topo(self, substrate, mapped_start_nodes, mapped_cdn_nodes, vhg_count, vcdn_count, delay,
                             hint_node_mappings=None):
        raise NotImplementedError("Must override methodB")

    def get_vhg(self):
        return get_nodes_by_type("VHG", self.servicetopo)

    def get_vcdn(self):
        return get_nodes_by_type("VCDN", self.servicetopo)

    def get_cdn(self):
        return get_nodes_by_type("CDN", self.servicetopo)

    def get_Starters(self):
        return [(s, self.servicetopo.node[s]["mapping"], self.servicetopo.node[s]["bandwidth"]) for s in
                get_nodes_by_type("S", self.servicetopo)]

    def get_CDN(self):
        return [(s, self.servicetopo.node[s]["mapping"], self.servicetopo.node[s]["bandwidth"]) for s in
                get_nodes_by_type("CDN", self.servicetopo)]

    def getServiceNodes(self):
        for node in self.servicetopo.nodes(data=True):
            yield node[0], node[1].get("cpu", 0), node[1].get("bandwidth", 0)

    def getServiceCDNNodes(self):
        cdns = self.get_cdn()
        for node in self.servicetopo.nodes(data=True):
            if node[0] in cdns:
                yield node[0], node[1].get("cpu", 0)

    def dump_edges(self):
        '''
        :return: [(start , end , bandwidth)]
        '''
        res = []
        for start, ends in self.servicetopo.edge.items():
            for end in ends:
                edge = self.servicetopo[start][end]
                res.append((start, end, edge.get("bandwidth", 0)))
        return res

    def getServiceCDNEdges(self):
        '''

        :return: start, end, edge["bandwidth"]
        '''
        for start, ends in self.servicetopo.edge.items():
            cdns = self.get_cdn()
            for end in [end for end in ends if end in cdns]:
                edge = self.servicetopo[start][end]
                yield start, end, edge.get("bandwidth", 0)

    def getServiceEdges(self):
        '''

        :return: start, end, edge["bandwidth"]
        '''
        for start, ends in self.servicetopo.edge.items():
            for end in ends:
                edge = self.servicetopo[start][end]
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
        for path, segments in self.delay_routes.items():
            for segment in segments:
                res.append((path, segment[0], segment[1]))

        return res