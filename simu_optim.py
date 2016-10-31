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
session = Session()
tenant = Tenant()
session.add(tenant)
slas = generate_random_slas(rs, su, count=args.sla_count, user_count=1000, max_start_count=args.max_start,
                            max_end_count=args.max_cdn, tenant=tenant)

for sla in slas:
    try:
        service_no_heuristic, count_embedding_no_heuristic = optimize_sla(sla, automatic=True, use_heuristic=False)
        service_no_heuristic_mapping_objective_function = service_no_heuristic.mapping.objective_function
    except ValueError as e:
        service_no_heuristic_mapping_objective_function = float("nan")

    try:
        service_yes_heuristic, count_embedding_yes_heuristic = optimize_sla(sla, automatic=True, use_heuristic=True)
        service_yes_heuristic_mapping_objective_function = service_yes_heuristic.mapping.objective_function

    except ValueError as e:
        service_yes_heuristic_mapping_objective_function = float("nan")

    try:
        service_yes_heuristic11, count_embedding_yes_heuristic11 = optimize_sla(sla, vhg_count=1, vcdn_count=1,
                                                                                automatic=False,
                                                                                use_heuristic=True)
        service_yes_heuristic11_mapping_objective_function = service_yes_heuristic11.mapping.objective_function
    except ValueError as e:
        service_yes_heuristic11_mapping_objective_function = float("nan")

    try:
        service_yes_heuristicNN, count_embedding_yes_heuristicNN = optimize_sla(sla, automatic=False,
                                                                                vhg_count=len(sla.get_start_nodes()),
                                                                                vcdn_count=len(sla.get_start_nodes()),
                                                                                use_heuristic=True)

        service_yes_heuristicNN_mapping_objective_function = service_yes_heuristicNN.mapping.objective_function

    except ValueError as e:
        service_yes_heuristicNN_mapping_objective_function = float("nan")

        # print ( "winner : %s" % str(service.id))
        # su.consume_service(service)
    print "#\t%s\t%s\t%s\t%lf\t%lf\t%lf\t%lf" % (su,
                                                 "_".join([sn.topoNode.name for sn in sla.get_start_nodes()]),
                                                 "_".join([sn.topoNode.name for sn in sla.get_cdn_nodes()]),
                                                 service_no_heuristic_mapping_objective_function,
                                                 service_yes_heuristic_mapping_objective_function,
                                                 service_yes_heuristic11_mapping_objective_function,
                                                 service_yes_heuristicNN_mapping_objective_function)

    

'''
service, count_embedding = create_sla(args.start, args.cdn, args.sourcebw, args.topo, 0,
                                                                    vhg_count=args.vhg, vcdn_count=args.vcdn,
                                                                    automatic=args.auto,
                                                                    use_heuristic=not args.disable_heuristic)
'''
