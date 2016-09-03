#!/usr/bin/env python

import argparse
import os
import sys

import numpy as np

from ..core.service import Service
from ..core.solver import solve
from ..core.substrate import Substrate

GEANT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/Geant2012.graphml')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return (name, spec)


parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument( "--just-topo", dest='just_topo', action='store_true')
parser.add_argument('--sla_delay', help="delay toward vCDN", default=30.0, type=float)
parser.add_argument('--start', metavar='S', type=str, nargs='+',
                    help='a list of starters')
parser.add_argument('--cdn', metavar='CDN', type=str, nargs='+',
                    help='a list of CDN')

parser.add_argument('--vcdnratio', help="the share of source traffic toward vcdn", default=0.35, type=float)
parser.add_argument('--sourcebw', help="cumulated source bw from every source", default=1000000000, type=int)
parser.add_argument('--topo', help="specify topo to use", default=('grid',["5","5"]), type=valid_topo)

args = parser.parse_args()

rs = np.random.RandomState()
su = Substrate.fromSpec(args.topo)

if args.just_topo:
    su.write()
    exit(0)

for s in args.start:
    assert s in su.nodesdict, "%s not in %s" % (s, su.nodesdict.keys())

for s in args.cdn:
    assert s in su.nodesdict

su.write()

best = sys.float_info.max
best_service = None
best_mapping = None
for vhg in range(1, len(args.start) + 1):
    for vcdn in range(1, min([len(args.start) + 1, vhg+1])):

        service = Service(args.sourcebw/len(args.start), vhg, args.sla_delay, args.vcdnratio, 5, 3, vcdn, args.start,
                          args.cdn, len(args.cdn), True)
        service.write()
        mapping = solve(service, su, preassign_vhg=True)
        if mapping is not None:
            if mapping.objective_function < best:
                best = mapping.objective_function
                best_service = service
                best_mapping=mapping

if not best_mapping is None:

    su.consume_service(best_service, best_mapping)
    su.write()
    best_mapping.save()
    sys.stdout.write("success: %e\n" % best_mapping.objective_function)
    with open(os.path.join(RESULTS_FOLDER, "best.mapping.data"),"w") as f:
        f.write("VMG,VCDN,CostFunction\n")
        f.write("%d,%d,%lf"%(best_service.vhgcount,best_service.vcdncount,best))

    exit(0)
else:
    sys.stdout.write("failure\n")
    # mapping = __solve(service, su,allow_violations=True)
    # if mapping:
    #    for index, violation in enumerate(mapping.violations,start=1):
    #        print("violation %d : %s" % (index,violation))
    exit(1)
