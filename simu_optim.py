#!/usr/bin/env python

import argparse
import logging
import os

from offline.core.sla import generate_random_slas
from offline.time.persistence import Tenant, Session
from offline.tools.ostep import clean_and_create_experiment
from offline.tools.ostep import optimize_sla


def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return (name, spec)


RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'offline/results')

logging.basicConfig(filename='simu.log', level="DEBUG", )

parser = argparse.ArgumentParser(description='run simu with solver')
parser.add_argument('--sla_count', type=int, help='number of sla to generate',
                    default=5)
parser.add_argument('--seed', type=int, help='seed for random state generation',
                    default=0)
parser.add_argument('--sla_delay', help="delay toward vCDN, float in ms", default=30.0, type=float)
parser.add_argument('--max_start', type=int, help='maximum number of starters',
                    default=5)
parser.add_argument('--max_cdn', type=int, help='maximum number of CDNs',
                    default=5)
parser.add_argument('--vcdnratio', help="the share of source traffic toward vcdn (default 0.35)", default=0.35,
                    type=float)
parser.add_argument('--sourcebw', help="cumulated source bw from every source (default 100 bits) ", default=100000000,
                    type=int)
parser.add_argument('--topo', help="specify topo to use", default=('grid', ["5", "5", "100000000", "10", "200"]),
                    type=valid_topo)
parser.add_argument('--disable-heuristic', dest="disable_heuristic", action="store_true")
parser.add_argument('--dest_folder', help="destination folder for restults", default=RESULTS_FOLDER)

args = parser.parse_args()

# create the topology
rs, su = clean_and_create_experiment(args.topo, args.seed)

slas = generate_random_slas(rs, su, count=args.sla_count, user_count=1000, max_start_count=args.max_start, max_end_count=args.max_cdn)

for sla in slas:
    service, count_embedding = optimize_sla(sla,
                                            automatic=True, use_heuristic=not args.disable_heuristic)

    # print ( "winner : %s" % str(service.id))
    su.consume_service(service)
    print "%s\t%lf" % (su, service.mapping.objective_function)

'''
service, count_embedding = create_sla(args.start, args.cdn, args.sourcebw, args.topo, 0,
                                                                    vhg_count=args.vhg, vcdn_count=args.vcdn,
                                                                    automatic=args.auto,
                                                                    use_heuristic=not args.disable_heuristic)
'''
