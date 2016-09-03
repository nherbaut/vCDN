#!/usr/bin/env python

import argparse
import os
import pickle
import sys

import numpy as np

from ..core.service import Service
from ..core.sla import generate_random_slas
from ..core.solver import solve
from ..core.substrate import Substrate
from ..time.persistence import session, Base, engine, drop_all, Tenant
RESULTS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return (name, spec)


Base.metadata.create_all(engine)
rs = np.random.RandomState(1)
# clear the db
drop_all()
tenant = Tenant(name="default")
session.add(tenant)
session.commit()

parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument('-d', "--dry-run", dest='dry', action='store_true')
parser.add_argument('--vhg', help="the number of failure until the algorithm stops", default=None)
parser.add_argument('--vcdn', help="number of VCDN", default=None)
parser.add_argument('--s', help="number of starter", default=1, type=int)
parser.add_argument('--cdn', help="number of cdn", default=1, type=int)
parser.add_argument('--reuse', help="Start from a new substrate", dest='reuse', action='store_true')
parser.add_argument('--topo', help="specify topo to use", default=('grid', (5,5)), type=valid_topo)
parser.add_argument('--spvhg-disable', help="Disable grouping vhg by shortest path", dest='spvhg_disable',
                    action='store_true')

parser.add_argument('--vhgpa-disable', help="Disable grouping vhg by shortest path", dest='vhgpa',
                    action='store_true')
parser.add_argument("--__solve-disable", help="no try to find solution", dest='solve_disable', action='store_true')

args = parser.parse_args()
dry = args.dry
spvhg_disable = args.spvhg_disable
vhgpa = args.vhgpa

rs = np.random.RandomState()

su = Substrate.fromSpec(args.topo)

session.add(su)
session.commit()

if args.solve_disable:
    print("Not tried to find a solution (--__solve-disable)")
    print("finish")
    exit(0)



sla = generate_random_slas(rs, su, 1, start_count=args.s,  end_count=args.cdn,tenant=tenant)[0]
session.add(sla)
session.commit()

slas_spec={sla.id:{"VHG":3,"VCDN":3}}
service = Service([sla], service_spec=slas_spec)
session.add(service)
session.commit()
service.__solve()


if service.mapping is not None:
    if not dry:
        su.consume_service(service)
        su.write()
        print("success %lf"%service.mapping.objective_function)

    exit(0)
else:
    sys.stdout.write("failure\n")
    # mapping = __solve(service, su,allow_violations=True)
    # if mapping:
    #    for index, violation in enumerate(mapping.violations,start=1):
    #        print("violation %d : %s" % (index,violation))
    exit(1)
