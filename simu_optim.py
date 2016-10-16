#!/usr/bin/env python
from random import random
from bisect import bisect_right
import numpy as np
import argparse
import logging
import os

from offline.tools.ostep import clean_and_create_experiment_and_optimize, clean_and_create_experiment

#http://nicky.vanforeest.com/probability/weightedRandomShuffling/weighted.html
def weighted_shuffle(a,w,rs):
    r = np.empty_like(a)
    cumWeights = np.cumsum(w)
    for i in range(len(a)):
         rnd = rs.uniform() * cumWeights[-1]
         j = bisect_right(cumWeights,rnd)
         r[i]=a[j]
         cumWeights[j:] -= w[j]
    return r

def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return (name, spec)


RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'offline/results')

logging.basicConfig(filename='simu.log', level="DEBUG", )

parser = argparse.ArgumentParser(description='run simu with solver')

parser.add_argument('--seed', type=int, help='seed for random state generation',
                    default=0)
parser.add_argument('--sla_delay', help="delay toward vCDN, float in ms", default=30.0, type=float)
parser.add_argument('--max_start', type=int, help='maximum number of starters',
                    default=5)
parser.add_argument('--max_cdn', type=int, help='maximum number of CDNs',
                    default=5)
parser.add_argument('--vcdnratio', help="the share of source traffic toward vcdn (default 0.35)", default=0.35,
                    type=float)
parser.add_argument('--sourcebw', help="cumulated source bw from every source (default 100 bits) ", default=100,
                    type=int)
parser.add_argument('--topo', help="specify topo to use", default=('grid', ["5", "5", "100000000", "10", "200"]),
                    type=valid_topo)
parser.add_argument('--disable-heuristic', dest="disable_heuristic", action="store_true")
parser.add_argument('--dest_folder', help="destination folder for restults", default=RESULTS_FOLDER)

args = parser.parse_args()

#create the topology
rs, su = clean_and_create_experiment(args.topo, args.seed)

#get the nodes and their total bw
nodes_by_degree = su.get_nodes_by_degree()
nodes_by_bw = su.get_nodes_by_bw()

cdns=[]
starts=[]
cdns=weighted_shuffle(nodes_by_degree.keys(),nodes_by_degree.values(),rs)[:args.max_cdn]
starts=weighted_shuffle(nodes_by_bw .keys(),nodes_by_bw .values(),rs)[-args.max_start:]

print cdns
print starts


'''
service, count_embedding = clean_and_create_experiment_and_optimize(args.start, args.cdn, args.sourcebw, args.topo, 0,
                                                                    vhg_count=args.vhg, vcdn_count=args.vcdn,
                                                                    automatic=args.auto,
                                                                    use_heuristic=not args.disable_heuristic)
'''
