#!/usr/bin/env python3
# run simulation for paper 5
# import simpy
# from offline.core.substrate import Substrate
import logging
import sys

import numpy as np
import pylru
import simpy
from numpy.random import RandomState
from offline.discrete import Topo
from offline.core.sla import generate_random_slas
from offline.core.substrate import Substrate
from offline.discrete.ContentHistory import ContentHistory
from offline.discrete.Contents import get_content_generator
from offline.discrete.utils import *
from offline.discrete.Generators import get_ticker
from offline.discrete.Monitoring import Monitoring
from offline.discrete.endUser import User
from offline.discrete.utils import CDNStorage
from offline.discrete.vCDN import vCDN
from offline.time.persistence import Session, Tenant
from offline.tools.ostep import clean_and_create_experiment

################################################
############ SETUP LOGGING######################
################################################
root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

################################################
############ SETUP TOPOLOGY ####################
################################################


link_id = "5511"
# link_id = "dummy"
cdn_count = 5
client_count = 1000
vcdn_count = 200
cache_size_vcdn = 300
vcdn_capacity = 300
cdn_capacity = 1000
zipf_param = 1.3
poisson_param = 0.1
max_time_experiment = 300
content_duration = 60
refresh_delay = 60
download_delay = 20
concurent_download = 5
vcdn_quantile = 0.8
cdn_quantile = 1
consumer_quantile = 0.1


# create the topology and the random state

def load_exising_experiment(link_id):
    session = Session()
    # first, if data_sum is already present, try with it
    tenant = session.query(Tenant).filter(Tenant.name == link_id).one()
    su = session.query(Substrate).one()
    rs = RandomState(seed=5)
    logging.debug("Data logged from DB")
    return tenant, su, rs


def create_new_experiment(link_id):
    session = Session()
    logging.info("Unexpected error:", sys.exc_info()[0])
    logging.debug("Failed to read data_sum from DB, reloading from file")
    if link_id == "dummy":
        rs, su = clean_and_create_experiment(("powerlaw", (200, 2, 0.3, 1, 1000000000, 20, 200,)), seed=5)
    else:
        rs, su = clean_and_create_experiment(("links", (link_id,)), 5)

    tenant = Tenant(name=link_id)
    session.add(tenant)
    session.add(su)
    session.flush()
    return tenant, su, rs


def create_sla(client_count, cdn_count, vcdn_count):
    slas = generate_random_slas(rs,
                                su,
                                count=1,
                                user_count=1000000,
                                max_start_count=client_count,
                                max_end_count=cdn_count + vcdn_count,
                                tenant=tenant,
                                min_start_count=client_count - 1,
                                min_end_count=cdn_count + vcdn_count - 1)

    session = Session()
    session.add_all(slas)
    session.flush()
    logging.debug("SLA saved")

    sla = slas[0]
    return sla


def get_servers_from_sla(sla):
    servers = [node.topoNode.name for node in sla.get_cdn_nodes()]
    cdns = servers[0:cdn_count]
    vcdns = servers[cdn_count:(cdn_count + vcdn_count)]
    return cdns, vcdns


def setup_servers(g, cdns, vcdns):
    for cdn in cdns:
        g.node[cdn]["storage"] = CDNStorage()

        g.node[cdn]["capacity"] = cdn_capacity
        g.node[cdn]["type"] = "CDN"

    for vcdn in vcdns:
        g.node[vcdn]["storage"] = pylru.lrucache(cache_size_vcdn)

        g.node[vcdn]["capacity"] = vcdn_capacity
        g.node[vcdn]["type"] = "vCDN"


# load topology data_sum
print("loading db")
# try:
#    tenant, su, rs = load_exising_experiment(link_id)
# except:
#    tenant, su, rs = create_new_experiment(link_id)
# print("loading db done")
# generate SLAS
# sla = create_sla(client_count, cdn_count, vcdn_count)


import networkx as nx
import operator
import os
import pandas as pd

name = "5511"
g = nx.Graph()
# load all the links
with open(os.path.join("offline/data", "links", "operator-%s.links" % name)) as f:
    for line in f.read().split("\n"):
        nodes = line.strip().split(" ")
        while len(nodes) >= 2:
            root = nodes.pop(0)
            for node in nodes:
                g.add_edge(root, node)

# take the biggest connected subgraph
g = max(list({sg: len(sg.nodes()) for sg in nx.connected_component_subgraphs(g)}.items()),
        key=operator.itemgetter(1))[0]
Topo.g=g
for e0, e1 in g.edges():
    g.edge[e0][e1]["bandwidth"] = g.degree(e0) * g.degree(e1) * 100000000000000

rs = RandomState(seed=5)


def get_nodes_by_weight(rs, g, count, quantile=1, weights="bandwidth", highest=True):
    if highest:
        mult = -1
    else:
        mult = 1
    nodes_by_degree = g.degree()

    nodes_df = pd.DataFrame(index=[x[0] for x in nodes_by_degree.items()], data=[x[1] for x in nodes_by_degree.items()])
    nodes_df_quantile = nodes_df[nodes_df < nodes_df.quantile(quantile)].dropna()

    return [a for a, b in
            sorted(nodes_df_quantile.to_dict()[0].items(), key=lambda x: mult * rs.uniform() * x[1])[0:count]]


cdns = get_nodes_by_weight(rs, g, cdn_count, quantile=cdn_quantile)
vcdns = get_nodes_by_weight(rs, g, vcdn_count, quantile=vcdn_quantile)
consumers = get_nodes_by_weight(rs, g, client_count, quantile=consumer_quantile, highest=False)

# setup servers capacity, storage...
setup_servers(g, cdns, vcdns)

contentHistory = ContentHistory()

content_draw = get_content_generator(rs, zipf_param, contentHistory, 5000000, 1, content_duration)

# contentHistory = get_updated_history(contentHistory, content)

# update_vcdn_storage(g, contentHistory)

# winner, price = create_content_delivery(g=g, peers=servers, content=content,consumer=consumer)

env = simpy.Environment()
the_time = 30

ticker = get_ticker(rs, poisson_param, )

while the_time < max_time_experiment:
    location = rs.choice(consumers)
    the_time = ticker() + the_time
    User(g, {"CDN": cdns, "VCDN": vcdns}, env, location, the_time, content_draw)

for vcdn in vcdns:
    vCDN(env, vcdn, g, contentHistory, refresh_delay=refresh_delay, download_delay=download_delay,
         concurent_download=concurent_download)


def capacity_vcdn_monitor():
    while True:
        yield env.timeout(1)
        res_cap_vcdn = []
        res_cap_cdn = []
        res_storage = []
        for vcdn in vcdns:
            res_cap_vcdn.append(g.node[vcdn]["capacity"])
            res_storage.append(len(list(g.node[vcdn]["storage"].keys())))

        for cdn in cdns:
            res_cap_cdn.append(g.node[cdn]["capacity"])

        Monitoring.push_average("VCDN.CAP", env.now, np.sum(res_cap_vcdn))
        Monitoring.push_average("VCDN.STORAGE", env.now, np.sum(res_storage))
        Monitoring.push_average("CDN.CAP", env.now, np.sum(res_cap_cdn))


env.process(capacity_vcdn_monitor())
env.run(until=max_time_experiment  +200)

Monitoring.getdf().to_csv("eval.csv")

