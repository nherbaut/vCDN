#!/usr/bin/env python3
# run simulation for paper 5
# import simpy
# from offline.core.substrate import Substrate
import logging
import random
import sys

from numpy.random import RandomState

from offline.core.sla import generate_random_slas
from offline.core.substrate import Substrate
from offline.discrete.Contents import Contents
from offline.discrete.utils import create_content_delivery, CDNStorage
from offline.time.persistence import Session, Tenant
from offline.tools.ostep import clean_and_create_experiment

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stderr)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

############"

contents = Contents()
session = Session()
link_id = "12322"
# create the topology and the random state

try:
    # first, if data is already present, try with it
    tenant = session.query(Tenant).filter(Tenant.name == link_id).one()
    su = session.query(Substrate).one()
    rs = RandomState()
    logging.debug("Data logged from DB")
except:
    logging.info("Unexpected error:", sys.exc_info()[0])
    logging.debug("Failed to read data from DB, reloading from file")
    rs, su = clean_and_create_experiment(("links", (link_id,)), int(random.uniform(1, 100)))
    tenant = Tenant(name=link_id)
    session.add(tenant)
    session.add(su)
    session.flush()
logging.debug("SLA generation")
slas = generate_random_slas(rs, su, count=1, user_count=1000000, max_start_count=100, max_end_count=5, tenant=tenant,
                            min_start_count=99, min_end_count=4)

session.add_all(slas)
session.flush()
logging.debug("SLA saved")

sla = slas[0]
logging.debug("Loading graph in memory")
g = su.get_nxgraph()

logging.debug("setup content and capacity")
cdns = [node.topoNode.name for node in sla.get_cdn_nodes()]
for cdn in cdns:
    g.node[cdn]["storage"] = CDNStorage()
    g.node[cdn]["capacity"] = 20000

success = 1.
trial = 1.
while success / trial > 0.8:
    try:

        trial += 1
        consumer = random.choice(sla.get_start_nodes()).topoNode.name
        winner, price = create_content_delivery(g=g, peers=cdns, content=contents.draw(), consumer=consumer)
        success += 1
        print("%lf\t%lf\t%.2f\t\tserved %s \t\tfrom %s for %lf" % (success ,trial,success / trial,winner[0][0], winner[-1][1], price))
    except Exception as e:
        #logging.error(e)
        #print("this is the end of time")
        pass

        # add the session and the tentant.
