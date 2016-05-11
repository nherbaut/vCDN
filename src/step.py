#!/usr/bin/env python

import argparse
import os
import pickle
import sys

import numpy as np
from service import Service
from sla import generate_random_slas
from solver import solve
from substrate import Substrate

parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument('-d', "--dry-run", dest='dry', action='store_true')
parser.add_argument('--vhg', help="the number of failure until the algorithm stops", default=None)
parser.add_argument('--vcdn', help="integer seed used for random number generation", default=None)
parser.add_argument('--reuse', help="Start from a new substrate", dest='reuse', action='store_true')
parser.add_argument('--spvhg-disable', help="Disable grouping vhg by shortest path", dest='spvhg_disable',
                    action='store_true')

parser.add_argument('--vhgpa-disable', help="Disable grouping vhg by shortest path", dest='vhgpa',
                    action='store_true')

args = parser.parse_args()
dry = args.dry
spvhg_disable = args.spvhg_disable
vhgpa=args.vhgpa

rs = np.random.RandomState()
if args.reuse:
    su = Substrate.fromFile()
else:
    su = Substrate.fromGraph(rs, 'Geant2012.graphml')
    #su=Substrate.fromSpec(3,4,10**9,1,100)

su.write()
if dry and not os.path.isfile("service.pickle"):
    print("must have a service.pickle to dry-run")
    exit(1)

elif dry:
    with open("service.pickle", "r") as f:
        service = pickle.load(f)
else:
    sla = generate_random_slas(rs, su, 1)[0]
    service = Service.fromSla(sla)

if spvhg_disable:
    Service.spvhg = False
else:
    Service.spvhg = True

if args.vhg is not None:
    if int(args.vhg) > len(service.start):
        print("warining, vhg_count greater that start count, decreased vhg coutn to %d " % len(service.start))
    service.vhgcount = min(len(service.start), int(args.vhg))
if args.vcdn is not None:
    service.vcdncount = int(args.vcdn)

with open("service.pickle", "w") as f:
    pickle.dump(service, f)

service.write()


mapping = solve(service, su,preassign_vhg=not vhgpa)

if not mapping is None:
    if not dry:
        su.consume_service(service, mapping)
        su.write()
    mapping.save()
    # os.remove("service.pickle")
    sys.stdout.write("success: %e\n" % mapping.objective_function)
    exit(0)
else:
    sys.stdout.write("failure\n")
    # mapping = solve(service, su,allow_violations=True)
    # if mapping:
    #    for index, violation in enumerate(mapping.violations,start=1):
    #        print("violation %d : %s" % (index,violation))
    exit(1)
