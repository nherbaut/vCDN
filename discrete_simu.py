#!/usr/bin/env python3
# run simulation for paper 5
# import simpy
# from offline.core.substrate import Substrate
import logging
import sys
import matplotlib.pyplot as plt
import matplotlib
import random
matplotlib.style.use('ggplot')

import pylru
import simpy
from numpy.random import RandomState

from offline.core.sla import generate_random_slas
from offline.core.substrate import Substrate
from offline.discrete.ContentHistory import ContentHistory
from offline.discrete.Monitoring import Monitoring
from offline.discrete.Contents import get_content_generator
from offline.discrete.Generators import get_ticker
from offline.discrete.endUser import User
from offline.discrete.utils import CDNStorage
from offline.discrete.vCDN import vCDN
from offline.time.persistence import Session, Tenant
from offline.tools.ostep import clean_and_create_experiment

################################################
############ SETUP LOGGING######################
################################################
root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

################################################
############ SETUP TOPOLOGY ####################
################################################


#link_id = "5511"
link_id = "dummy"
cdn_count = 10
client_count = 1000
vcdn_count = 100
cache_size_vcdn = 15
vcdn_capacity = 100
cdn_capacity = 1000
zipf_param = 1.1
poisson_param = 1
max_time_experiment = 1500
content_duration=100
refresh_delay = 60
download_delay = 10


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
        rs, su = clean_and_create_experiment(("powerlaw", (2000, 2, 0.3, 1, 1000000000, 20, 200,)), seed=5)
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
try:
    tenant, su, rs = load_exising_experiment(link_id)
except:
    tenant, su, rs = create_new_experiment(link_id)

# generate SLAS
sla = create_sla(client_count, cdn_count, vcdn_count)

# load topo into networkx graph
g = su.get_nxgraph()

# get servers
cdns, vcdns = get_servers_from_sla(sla)

# setup servers capacity, storage...
setup_servers(g, cdns, vcdns)

contentHistory = ContentHistory()

content_draw = get_content_generator(rs, zipf_param, contentHistory, 5000000, 1,content_duration)

consumers = [node.topoNode.name for node in sla.get_start_nodes()]

# contentHistory = get_updated_history(contentHistory, content)

# update_vcdn_storage(g, contentHistory)

# winner, price = create_content_delivery(g=g, peers=servers, content=content,consumer=consumer)

env = simpy.Environment()
the_time = 0

ticker = get_ticker(rs, poisson_param, )

while the_time < max_time_experiment:
    location = rs.choice(consumers)
    the_time = ticker() + the_time
    User(g, cdns + vcdns, env, location, the_time, content_draw)

for vcdn in vcdns:
    vCDN(env, vcdn, g, contentHistory, refresh_delay=refresh_delay, download_delay=download_delay)
env.run(until=max_time_experiment * 2)

Monitoring.getdf().to_csv("eval.csv")

