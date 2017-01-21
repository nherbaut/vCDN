#!/usr/bin/env python

import argparse
import os

import pickle
import sys
import shutil
import numpy as np


from ..core.service import Service
from ..core.sla import generate_random_slas
from ..core.solver import solve
from ..core.substrate import Substrate, RESULTS_FOLDER
from offline.core.sla import Sla
GEANT_PATH=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/Geant2012.graphml')


def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return (name, spec)


parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument( "--just-topo", dest='just_topo', action='store_true')

parser.add_argument('--vhg', help="the number of failure until the algorithm stops", default=1,type=int)
parser.add_argument('--vcdn', help="number of VCDN", default=1,type=int)
parser.add_argument('--sla_delay', help="delay toward vCDN", default=30.0,type=float)
parser.add_argument('--start', metavar='S', type=str, nargs='+',
                    help='a list of starters')
parser.add_argument('--cdn', metavar='CDN', type=str, nargs='+',
                    help='a list of CDN')

parser.add_argument('--vcdnratio', help="the share of source traffic toward vcdn", default=0.35,type=float)
parser.add_argument('--sourcebw', help="cumulated source bw from every source", default=1000000000,type=int)
parser.add_argument('--topo', help="specify topo to use", default=('grid',["5","5"]), type=valid_topo)


args = parser.parse_args()



rs = np.random.RandomState()
su = Substrate.fromSpec(args.topo)


if args.just_topo:
    su.write()
    shutil.copyfile(os.path.join(RESULTS_FOLDER,"substrate.edges.data"), os.path.join(RESULTS_FOLDER,"substrate.edges.empty.data"))
    exit(0)


for s in args.start:
    assert s in su.nodesdict , "%s not in %s" % (s,list(su.nodesdict.keys()))

for s in args.cdn:
    assert s in su.nodesdict

su.write()
shutil.copyfile(os.path.join(RESULTS_FOLDER,"substrate.edges.data"), os.path.join(RESULTS_FOLDER,"substrate.edges.empty.data"))

service=Service(args.sourcebw/len(args.start), args.vhg, args.sla_delay, args.vcdnratio, 5, 3, args.vcdn, args.start,
                 args.cdn, len(args.cdn), True)
service.write()


mapping = solve(service, su,preassign_vhg=True)

if not mapping is None:

    su.consume_service(service, mapping)
    su.write()
    mapping.save()
    # os.remove("service.pickle")
    sys.stdout.write("success: %e\n" % mapping.objective_function)
    exit(0)
else:
    sys.stdout.write("failure\n")
    exit(1)
