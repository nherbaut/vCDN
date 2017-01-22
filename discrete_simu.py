#!/usr/bin/env python3
# run simulation for paper 5
# import simpy
# from offline.core.substrate import Substrate
import logging
import sys

import pandas as pd
import pylru
import simpy
from numpy.random import RandomState

from offline.core.sla import generate_random_slas
from offline.core.substrate import Substrate
from offline.discrete.ContentHistory import ContentHistory
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

ch = logging.StreamHandler(sys.stderr)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

################################################
############ SETUP TOPOLOGY ####################
################################################


# link_id = "5511"
link_id = "dummy"
cdn_count = 0
client_count = 100
vcdn_count = 10


# create the topology and the random state

def load_exising_experiment(link_id):
    session = Session()
    # first, if data is already present, try with it
    tenant = session.query(Tenant).filter(Tenant.name == link_id).one()
    su = session.query(Substrate).one()
    rs = RandomState(seed=5)
    logging.debug("Data logged from DB")
    return tenant, su, rs


def create_new_experiment(link_id):
    session = Session()
    logging.info("Unexpected error:", sys.exc_info()[0])
    logging.debug("Failed to read data from DB, reloading from file")
    # rs, su = clean_and_create_experiment(("links", (link_id,)), int(random.uniform(1, 100)))
    rs, su = clean_and_create_experiment(("powerlaw", (500, 2, 0.3, 1, 1000000000, 20, 200,)), seed=5)
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
    return servers, cdns, vcdns


def setup_servers(g, cdns, vcdns):
    for cdn in cdns:
        g.node[cdn]["storage"] = CDNStorage()
        g.node[cdn]["capacity"] = 200
        g.node[cdn]["type"] = "CDN"

    for vcdn in vcdns:
        g.node[vcdn]["storage"] = pylru.lrucache(20)
        g.node[vcdn]["capacity"] = 100
        g.node[vcdn]["type"] = "vCDN"




def update_vcdn_storage(g, contentHistory):
    for vcdn in vcdns:
        for content in get_popular_contents(contentHistory, windows=200, count=5):
            g.node[vcdn]["storage"][content] = True


# load topology data
try:
    tenant, su, rs = load_exising_experiment(link_id)
except:
    tenant, su, rs = create_new_experiment(link_id)

# generate SLAS
sla = create_sla(client_count, cdn_count, vcdn_count)

# load topo into networkx graph
g = su.get_nxgraph()

# get servers
servers, cdns, vcdns = get_servers_from_sla(sla)

# setup servers capacity, storage...
setup_servers(g, cdns, vcdns)

contentHistory = ContentHistory()

content_draw = get_content_generator(rs, 1.1, contentHistory)

consumers = [node.topoNode.name for node in sla.get_start_nodes()]

# contentHistory = get_updated_history(contentHistory, content)

# update_vcdn_storage(g, contentHistory)

# winner, price = create_content_delivery(g=g, peers=servers, content=content,consumer=consumer)

env = simpy.Environment()
the_time = 0
ticker = get_ticker(rs, 1, )
while the_time < 3000:
    location = rs.choice(consumers)
    the_time = ticker() + the_time
    User(env, location, the_time, content_draw, content_duration=120)

for server in servers:
    vCDN(env, server, g, contentHistory)
env.run(until=3000)
