#!/usr/bin/env python
# run simulation for paper 5
# import simpy
# from offline.core.substrate import Substrate
import logging
import random

import networkx as nx
import numpy as np
from numpy.random import RandomState

from offline.core.sla import generate_random_slas, Sla
from offline.core.substrate import Substrate
from offline.time.persistence import Session, Tenant
from offline.tools.ostep import clean_and_create_experiment
from functools import lru_cache

class NotEnoughBandwidthError(Exception):
    pass


@lru_cache(maxsize=200)
def get_nearest_cdn_and_path(tn, cdns):
    return min(sorted({cdn: nx.shortest_path(g, tn, cdn) for cdn in cdns}.items()),
               key=lambda x: len(x[1]))


def tn_cdn(tn, cdns, g, bw, install=True):
    best_cdn, interm_nodes = get_nearest_cdn_and_path(tn, frozenset(cdns))
    path = list(zip(interm_nodes, interm_nodes[1:]))
    tn_cdn_with_path(tn, path, g, bw, install)
    return path


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


############"

logging.basicConfig(filename='simu.log', level="DEBUG", )
session = Session()
link_id = "5511"
# create the topology and the random state

try:
    # first, if data is already present, try with it
    tenant = session.query(Tenant).filter(Tenant.name == link_id).one()
    su = session.query(Substrate).one()
    rs = RandomState()
    slas = [session.query(Sla).one()]
    logging.debug("Data logged from DB")
except:
    logging.debug("Failed to read data from DB, reloading from file")
    rs, su = clean_and_create_experiment(("links", (link_id,)), int(random.uniform(1, 100)))
    tenant = Tenant(name=link_id)
    session.add(tenant)
    session.add(su)
    session.flush()
    slas = generate_random_slas(rs, su, count=1, user_count=1000000, max_start_count=5, max_end_count=5, tenant=tenant,
                                min_start_count=4, min_end_count=4)
    session.add_all(slas)
    session.flush()
sla = slas[0]
cdns = [node.topoNode.name for node in sla.get_cdn_nodes()]
g = su.get_nxgraph()
original = np.sum(d[2]["bandwidth"] for d in g.edges(data=True))

try:
    while True:
        tn = random.choice(sla.get_start_nodes()).topoNode.name
        path = tn_cdn(tn, cdns, g, 100000000, install=True)
        print("%s to %s" % (tn, path[-1][1]))
        # remaining = np.sum(d[2]["bandwidth"] for d in g.edges(data=True))
        # print("%lf \t\t %lf\n" % (remaining,(original - remaining ) / original))
        print("%lf remaining on path" % min(g.edge[n0][n1]["bandwidth"] for n0, n1 in path))

except NotEnoughBandwidthError as e:
    print("this is the end of time")


# add the session and the tentant.
