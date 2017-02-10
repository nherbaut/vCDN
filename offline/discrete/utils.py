import functools
import logging
import sys

import networkx as nx
import numpy as np

from offline.core.utils import red
from offline.discrete import Topo
from offline.discrete.Monitoring import Monitoring


class CDNStorage:
    def __getitem__(self, item):
        return True

    def get(self, key, default=None):
        return True

    def keys(self):
        return ['CDN has all']


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

        if node1 != node2 and g.edge[node1][node2]["bandwidth"] < bw:
            return False
    return True


def get_price_from_path(path, price_mult):
    return 2 + len(path) * price_mult


@functools.lru_cache(maxsize=None)
def p2p_get_shortest_path(peer1, peer2):
    g = Topo.g
    iterim_nodes = nx.shortest_path(g, peer1, peer2)
    return list(zip(iterim_nodes, iterim_nodes[1:]))


def consume_content_delivery(env, g, consumer, path, bw, capacity):
    if len(path) > 0:  # remote content
        producer = path[-1][1]
        # consume for LRU

        g.node[producer]["capacity"] = g.node[producer]["capacity"] - capacity
        for node1, node2 in path:
            if node1 != node2:
                g.edge[node1][node2]["bandwidth"] = g.edge[node1][node2]["bandwidth"] - bw

    else:

        path.append((consumer, consumer))


class NoPeerAvailableException(Exception):
    pass


def release_content_delivery(env, g, consumer, winner, bw, capacity):
    consume_content_delivery(env, g, consumer, winner, -bw, -capacity)


def create_content_delivery(env, g, servers, content, consumer, bw=5000000, capacity=1):
    best_prices = {}
    for key, peers in servers.items():
        if len(peers)==0:
            continue
        try:

            if key == "CDN":
                price_mult = 1.3
            elif key == "VCDN":
                price_mult = 1
            elif key == "MUCDN":
                price_mult = 1

            peers_with_content = list(get_peers_with_content(g, peers, content))

            Monitoring.push_average("AVG.PEER_WITH_CONTENT.%s" % key, env.now,
                                    np.sum([g.node[peer].get("capacity", 0) for peer in peers_with_content]))

            Monitoring.push_average("AVG.PEER_WITH_CONTENT.RATIO.%s" % key, env.now,
                                    len([g.node[peer] for peer in peers_with_content])/len(peers))

            peers_with_content_and_capacity = get_peers_with_capacity(g, peers_with_content, capacity)
            peers_with_content_and_capacity = list(peers_with_content_and_capacity)
            Monitoring.push_average("AVG.PEER_WITH_CONTENT_CAPACITY.%s" % key, env.now,
                                    np.sum(
                                        [g.node[peer].get("capacity", 0) for peer in peers_with_content_and_capacity]))

            peers_with_capacity = get_peers_with_capacity(g, peers, capacity)
            peers_with_capacity = list(peers_with_capacity)
            Monitoring.push_average("AVG.PEER_WITH_CAPACITY.%s" % key, env.now,
                                    np.sum(
                                        [g.node[peer].get("capacity", 0) for peer in peers_with_capacity]))

            valid_path_prices = [(path, get_price_from_path(path, price_mult)) for path in
                                 [p2p_get_shortest_path(consumer, server) for server in peers_with_content_and_capacity]
                                 if get_path_has_bandwidth(g, path, bw)]
            if len(valid_path_prices) == 0:
                continue

            average_price = np.mean([v for k, v in valid_path_prices])

            Monitoring.push_average("AVG.PRICE.%s" % key, env.now, average_price)
            Monitoring.push_average("MIN.PRICE.%s" % key, env.now, min(valid_path_prices, key=lambda x: x[1])[1])
            Monitoring.push_average("MAX.PRICE.%s" % key, env.now, max(valid_path_prices, key=lambda x: x[1])[1])
            Monitoring.push_average("MEDIAN.PRICE.%s" % key, env.now,
                                    np.median([v[1] for v in valid_path_prices]))
            # Monitoring.push_average("MEAN.PRICE.%s" % key, env.now, np.mean(valid_path_prices, key=lambda x: -x[1])[1])

            best_prices[key] = min(valid_path_prices, key=lambda x: x[1])
        except:
            print(sys.exc_info())
            print("oups")
            pass

    valid_path_prices = best_prices.values()
    if len(valid_path_prices) == 0:
        logging.debug("content delivery %s" % (red("MISS")))
        raise NoPeerAvailableException("No peer available")

    winner, min_price_all = min(valid_path_prices, key=lambda x: x[1])
    Monitoring.push_average("MIN.PRICE.ALL", env.now, min_price_all)

    consume_content_delivery(env, g, consumer, winner, bw, capacity)

    if len(winner) > 0:
        # update storage for LRU, if not on the same host
        producer = winner[-1][1]
        _ = g.node[producer]["storage"][content]
    return winner, average_price
