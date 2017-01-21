import functools

import networkx as nx


class CDNStorage:
    def __getitem__(self, item):
        return True

    def get(self, key, default=None):
        return True


def get_popular_contents(dataframe, windows=200, count=5):
    '''

    :param dataframe: the dataframe containing historic data
    :param windows: last *windows* observations to consider
    :param count: top *count* content id
    :return: a numpy.ndarray containing the values, ordered
    '''
    return dataframe.tail(windows)[0].value_counts().index[:count].values


def tn_cdn_with_path(path, g, bw, install=True):
    # removing bw
    for node1, node2 in path:
        if install:
            if g.edge[node1][node2]["bandwidth"] > bw:
                g.edge[node1][node2]["bandwidth"] = g.edge[node1][node2]["bandwidth"] - bw
                g.node[node1]["routes"] = g.node[node1].get("routes", 0) + 1
            else:
                raise NotEnoughBandwidthError()
        else:
            g.edge[node1][node2]["bandwidth"] = g.edge[node1][node2]["bandwidth"] + bw
            g.node[node1]["routes"] = g.node[node1].get("routes", 0) - 1


def get_peers_with_capacity(g, peers, capacity):
    for peer in peers:
        if g.node[peer]["capacity"] >= capacity:
            yield peer


def get_peers_with_content(g, peers, content):
    for peer in peers:
        if g.node[peer]["storage"].get(content) is not None:
            yield peer


def get_path_has_bandwidth(g, path, bw):
    for node1, node2 in path:
        if g.edge[node1][node2]["bandwidth"] < bw:
            return False
    return True


def get_price_from_path(path):
    return len(path)


@functools.lru_cache(maxsize=2000)
def p2p_get_shortest_path(g, peer1, peer2):
    iterim_nodes = nx.shortest_path(g, peer1, peer2)
    return list(zip(iterim_nodes, iterim_nodes[1:]))


def consume_content_delivery(g, path, bw, capacity):
    consumer = path[0][0]
    producer = path[-1][1]

    g.node[producer]["capacity"] = g.node[producer]["capacity"] - capacity
    for node1, node2 in path:
        g.edge[node1][node2]["bandwidth"] = g.edge[node1][node2]["bandwidth"] - bw


def create_content_delivery(g, peers, content, consumer, bw=5000000, capacity=1):
    peers_with_content = get_peers_with_content(g, peers, content)
    peers_with_content_and_capacity = get_peers_with_capacity(g, peers_with_content, capacity)

    valid_path_prices = [(path, get_price_from_path(path)) for path in
                         [p2p_get_shortest_path(g, consumer, server) for server in peers_with_content_and_capacity]
                         if get_path_has_bandwidth(g, path, bw)]

    if len(valid_path_prices) == 0:
        raise Exception("No peer available")

    winner, price = min(valid_path_prices, key=lambda x: x[1])

    consume_content_delivery(g, winner, bw, capacity)
    return winner, price
