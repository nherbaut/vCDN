#!/usr/bin/env python3
# run simulation for paper 5
# import simpy
# from offline.core.substrate import Substrate
import logging
import random
import sys

import pandas as pd
import pylru
from numpy.random import RandomState

from offline.core.sla import generate_random_slas
from offline.core.substrate import Substrate
from offline.core.utils import red
from offline.discrete.Contents import get_content_generator
from offline.discrete.utils import CDNStorage, create_content_delivery, get_popular_contents, NoPeerAvailableException
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


link_id = "5511"
# link_id = "dummy"
cdn_count = 0
client_count = 100
vcdn_count = 10


# create the topology and the random state

def load_exising_experiment(link_id):
    session = Session()
    # first, if data is already present, try with it
    tenant = session.query(Tenant).filter(Tenant.name == link_id).one()
    su = session.query(Substrate).one()
    rs = RandomState()
    logging.debug("Data logged from DB")
    return tenant, su, rs


def create_new_experiment(link_id):
    session = Session()
    logging.info("Unexpected error:", sys.exc_info()[0])
    logging.debug("Failed to read data from DB, reloading from file")
    rs, su = clean_and_create_experiment(("links", (link_id,)), int(random.uniform(1, 100)))
    # rs, su = clean_and_create_experiment(("powerlaw", (500, 2, 0.3, 1, 1000000000, 20, 200,)),                                         int(random.uniform(1, 100)))
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


def get_updated_history(df, c):
    return pd.concat([df, pd.DataFrame([content])])


# load topology data
try:
    tenant, su, rs = load_exising_experiment(link_id)
except:
    tenant, su, rs = create_new_experiment(link_id)

content_draw = get_content_generator(rs, 1.1)

# generate SLAS
sla = create_sla(client_count, cdn_count, vcdn_count)

# load topo into networkx graph
g = su.get_nxgraph()

# get servers
servers, cdns, vcdns = get_servers_from_sla(sla)

# setup servers capacity, storage...
setup_servers(g, cdns, vcdns)

contentHistory = pd.DataFrame()
success = 1.
trial = 1.


def update_vcdn_storage(g, contentHistory):
    for vcdn in vcdns:
        for content in get_popular_contents(contentHistory, windows=200, count=5):
            g.node[vcdn]["storage"][content] = True


while trial < 10000:
    try:

        trial += 1
        consumer = random.choice(sla.get_start_nodes()).topoNode.name
        content = content_draw()

        contentHistory = get_updated_history(contentHistory, content)

        if trial % 200 == 0:
            update_vcdn_storage(g, contentHistory)

        winner, price = create_content_delivery(g=g, peers=servers, content=content, consumer=consumer)
        success += 1

    except NoPeerAvailableException as e:
        logging.debug("%s" % red("No Hit"))
