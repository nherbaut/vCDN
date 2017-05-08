#!/usr/bin/env python3
# run simulation for paper 5
# import simpy
# from offline.core.substrate import Substrate

import simpy
from numpy.random import RandomState
import pylru
from offline.core.sla import generate_random_slas
from offline.core.substrate import Substrate
from offline.core.utils import printProgress
from offline.discrete.ContentHistory import ContentHistory
from offline.discrete.Contents import get_content_generator
from offline.discrete.Generators import get_ticker
from offline.discrete.TE import TE
from offline.discrete.endUser import User
from offline.discrete.utils import *
from offline.discrete.utils import CDNStorage
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
#link_id = "dummy"

# CDN
cdn_count = 6
cdn_capacity = 500
cdn_quantile_up = 0.9
cdn_quantile_down = 0.8

# VCDN
vcdn_count = 100
vcdn_capacity = 30
vcdn_quantile_up = 0.9
vcdn_quantile_down = 0.4
vcdn_cache_size = 1000
vcdn_refresh_delay = 240
vcdn_download_delay = 60
vcdn_concurent_download = 30

# muCDN
mucdn_count = 500
mucdn_capacity = 4
mucdn_quantile_up = 0.5
mucdn_quantile_down = 0.0
mucdn_cache_size = 30
mucdn_refresh_delay = 240
mucdn_download_delay = 100
mucdn_concurent_download = 1

# CLIENTS
client_count = 1500
consumer_quantile_up = 0.5
consumer_quantile_down = 0

# SIMULATION
zipf_param = 1.2
poisson_param = 0.1
max_time_experiment = 2000
content_duration = 200

# CONTENT
POPULAR_WINDOWS_SIZE = 500
POPULAR_HISTORY_COUNT = 30



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
        print("powerlaw graph selecteds")
        rs, su = clean_and_create_experiment(("powerlaw", (50, 2, 0.3, 1, 500000000, 20, 200,)), seed=5)
    else:
        print("links %s graph selected" % link_id)
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


def setup_nodes(g):
    for cdn in cdns:
        g.node[cdn]["storage"] = CDNStorage()
        g.node[cdn]["color"] = "#ff0000"
        g.node[cdn]["capacity"] = cdn_capacity
        g.node[cdn]["size"] = 50
        g.node[cdn]["type"] = "CDN"

    for vcdn_node in vcdns:
        g.node[vcdn_node]["storage"] = pylru.lrucache(vcdn_cache_size)
        #g.node[vcdn_node]["storage"] = CDNStorage()
        g.node[vcdn_node]["capacity"] = vcdn_capacity
        g.node[vcdn_node]["type"] = "VCDN"
        g.node[vcdn_node]["color"] = "#00ff00"
        g.node[vcdn_node]["size"] = 20

    for mucdn_node in mucdns:
        g.node[mucdn_node]["storage"] = pylru.lrucache(mucdn_cache_size)
        #g.node[mucdn_node]["storage"] = CDNStorage()
        g.node[mucdn_node]["capacity"] = mucdn_capacity
        g.node[mucdn_node]["size"] = 10
        g.node[mucdn_node]["type"] = "MUCDN"
        g.node[mucdn_node]["color"] = "#aaaaff"

    for consumer in consumers:
        g.node[consumer]["color"] = "#000000"
        g.node[consumer]["size"] = 5
        g.node[mucdn_node]["type"] = "CONSUMER"


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

g = nx.Graph()
# load all the links

if link_id == "dummy":
    print("powerlaw graph selecteds")
    _, su = clean_and_create_experiment(("powerlaw", (2000, 3, 0.5, 1, 1000000000, 20, 200,)), seed=6)
    g = su.get_nxgraph()

else:
    print("links %s graph selected" % link_id)
    with open(os.path.join("offline/data", "links", "operator-%s.links" % link_id)) as f:
        for line in f.read().split("\n"):
            nodes = line.strip().split(" ")
            while len(nodes) >= 2:
                root = nodes.pop(0)
                for node in nodes:
                    g.add_edge(root, node)

# take the biggest connected subgraph
g = max(list({sg: len(sg.nodes()) for sg in nx.connected_component_subgraphs(g)}.items()),
        key=operator.itemgetter(1))[0]
Topo.g = g
for e0, e1 in g.edges():
    g.edge[e0][e1]["bandwidth"] = g.degree(e0) * g.degree(e1) * 100000000000000

rs = RandomState(seed=5)


def random_with_quantile(rs, g, count, quantile_up=1.0, quantile_down=0.0, forbidden=[]):
    nodes_by_degree = g.degree()

    nodes_df = pd.DataFrame(index=[x[0] for x in nodes_by_degree.items()], data=[x[1] for x in nodes_by_degree.items()])

    nodes_df_quantile = nodes_df[
        (nodes_df <= nodes_df.quantile(quantile_up)) & (nodes_df >= nodes_df.quantile(quantile_down))].dropna()
    nodes_df_quantile = nodes_df_quantile.drop(forbidden, errors="ignore")

    candidates = list(nodes_df_quantile.index)
    rs.shuffle(candidates)
    return candidates[0:count]


def get_nodes_by_weight(rs, g, count, quantile=1.0, weights="bandwidth", highest=True, forbidden=[]):
    if highest:
        mult = -1
    else:
        mult = 1
    nodes_by_degree = g.degree()

    nodes_df = pd.DataFrame(index=[x[0] for x in nodes_by_degree.items()], data=[x[1] for x in nodes_by_degree.items()])

    nodes_df_quantile = nodes_df[nodes_df <= nodes_df.quantile(quantile)].dropna()
    nodes_df_quantile = nodes_df_quantile.drop(forbidden, errors="ignore")

    # return [a for a, b in             sorted(nodes_df_quantile.to_dict()[0].items(), key=lambda x: mult * rs.uniform() * x[1])[0:count]]
    return rs.shuffle(nodes_df_quantile)


assigned_nodes = []
# cdns = get_nodes_by_weight(rs, g, cdn_count, quantile=cdn_quantile, forbidden=assigned_nodes)
cdns = random_with_quantile(rs, g, cdn_count, quantile_up=cdn_quantile_up, quantile_down=cdn_quantile_down,
                            forbidden=assigned_nodes)
assigned_nodes += cdns
# vcdns = get_nodes_by_weight(rs, g, vcdn_count, quantile=vcdn_quantile, forbidden=assigned_nodes)
vcdns = random_with_quantile(rs, g, vcdn_count, quantile_up=vcdn_quantile_up, quantile_down=vcdn_quantile_down,
                             forbidden=assigned_nodes)
assigned_nodes += vcdns
# mucdns = get_nodes_by_weight(rs, g, mucdn_count, quantile=mucdn_quantile, forbidden=assigned_nodes)
mucdns = random_with_quantile(rs, g, mucdn_count, quantile_up=mucdn_quantile_up, quantile_down=mucdn_quantile_down,
                              forbidden=assigned_nodes)
assigned_nodes += mucdns
# consumers = get_nodes_by_weight(rs, g, client_count, quantile=consumer_quantile, highest=False,forbidden = assigned_nodes)

consumers = random_with_quantile(rs, g, client_count, quantile_up=consumer_quantile_up,
                                 quantile_down=consumer_quantile_down, forbidden=assigned_nodes)

print("cdn %d\tvcdn %d\tmucdn %d\t clients %d" % (len(cdns), len(vcdns), len(mucdns), len(consumers)))

# setup servers capacity, storage...
nx.set_node_attributes(g, 'color', "#bbbbbb")
nx.set_node_attributes(g, 'size', 1)
nx.set_node_attributes(g, 'users', 0)
setup_nodes(g)

# copied_graph = g.copy()
#nx.set_node_attributes(g, 'storage', 0)
#nx.write_graphml(g, path="graph.graphml")
#exit(-1)
# print("graph saved in graphml")

contentHistory= ContentHistory(windows=POPULAR_WINDOWS_SIZE, count=POPULAR_HISTORY_COUNT)

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
    User(g, {"CDN": cdns, "VCDN": vcdns, "MUCDN": mucdns}, env, location, the_time, content_draw)

for vcdn in vcdns:
    TE(rs, env, vcdn, g, contentHistory, refresh_delay=vcdn_refresh_delay, download_delay=vcdn_download_delay,
       concurent_download=vcdn_concurent_download)

for mucdn in mucdns:
    TE(rs, env, mucdn, g, contentHistory, refresh_delay=mucdn_refresh_delay, download_delay=mucdn_download_delay,
       concurent_download=mucdn_concurent_download)


def capacity_vcdn_monitor():
    while True:
        yield env.timeout(11)
        res_cap_vcdn = []
        res_cap_mucdn = []
        res_cap_cdn = []
        res_storage_vcdn = []
        res_storage_mucdn = []
        for vcdn in vcdns:
            res_cap_vcdn.append(g.node[vcdn]["capacity"])
            res_storage_vcdn.append(len(list(g.node[vcdn]["storage"].keys())))
        for mucdn in mucdns:
            res_cap_mucdn.append(g.node[mucdn]["capacity"])
            res_storage_mucdn.append(len(list(g.node[mucdn]["storage"].keys())))

        for cdn in cdns:
            res_cap_cdn.append(g.node[cdn]["capacity"])

        Monitoring.push_average("CAP.VCDN", env.now, np.sum(res_cap_vcdn))
        Monitoring.push_average("STORAGE.VCDN", env.now, np.sum(res_storage_vcdn))

        Monitoring.push_average("CAP.MUCDN", env.now, np.sum(res_cap_mucdn))
        Monitoring.push_average("STORAGE.MUCDN", env.now, np.sum(res_storage_mucdn))

        Monitoring.push_average("CAP.CDN", env.now, np.sum(res_cap_cdn))

        Monitoring.push_average("AVG.USERS.ALL", env.now, np.sum([v[1].get("users", 0) for v in g.nodes(data=True)]))

        for te_type in ["CDN", "VCDN", "MUCDN"]:
            Monitoring.push_average("AVG.USERS.%s" % te_type, env.now,
                                    np.sum([v[1].get("users", 0) for v in g.nodes(data=True) if
                                            v[1].get("type", "client") == te_type]))


env.process(capacity_vcdn_monitor())


def progress_display():
    while True:
        yield env.timeout(30)
        printProgress(env.now, max_time_experiment + content_duration)

    pass


env.process(progress_display())
env.run(until=max_time_experiment + content_duration)
Monitoring.getdf().to_csv("eval.csv")
print("\n%s" % str(p2p_get_shortest_path.cache_info()))
os.system("say 'it is over, thanks for waiting'")
