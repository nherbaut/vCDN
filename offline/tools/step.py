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
from ..db.persistance import DAO
GEANT_PATH=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/Geant2012.graphml')
RESULTS_PATH=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../results')


def valid_grid(gridspec):
    try:
        grid=[int(x) for x in gridspec.split("x")]
        if len(grid)!=2:
            raise ValueError
        else:
            return grid

    except ValueError:
        msg = "Not a valid grid: '{0}', should axb with a,b > 0 .".format(gridspec)
        raise argparse.ArgumentTypeError(msg)

def do_step(dry,spvhg_disable,vhgpa,reuse,grid,s,cdn,vhg,vcdn):
    dry = dry
    spvhg_disable = spvhg_disable
    vhgpa=vhgpa

    rs = np.random.RandomState()
    if reuse:
        su = Substrate.fromFile()
    else:
        if grid is not None:
            x,y=grid
            su=Substrate.fromSpec(x,y,10**10,1,100)
        else:
            su = Substrate.fromGraph(rs, GEANT_PATH)


    su.write()
    if dry and not os.path.isfile(os.path.join(RESULTS_PATH,"service.pickle")):
        print("must have a service.pickle to dry-run")
        exit(1)

    elif dry:
        with open(os.path.join(RESULTS_PATH,"service.pickle"), "r") as f:
            service = pickle.load(f)
    else:
        sla = generate_random_slas(rs, su, 1,start_count=s,max_cdn_to_use=cdn,end_count=cdn)[0]

        service = Service.fromSla(sla)

    if spvhg_disable:
        service.spvhg = False
    else:
        service.spvhg = True

    if vhg is not None:
        if int(vhg) > len(service.start):
            print("warining, vhg_count greater that start count, decreased vhg coutn to %d " % len(service.start))
        service.vhgcount = min(len(service.start), int(vhg))
    if vcdn is not None:
        service.vcdncount = int(vcdn)

    with open(os.path.join(RESULTS_PATH,"service.pickle"), "w") as f:
        pickle.dump(service, f)

    service.write()


    mapping = solve(service, su,preassign_vhg=not vhgpa)

    if not mapping is None:
        if not dry:
            su.consume_service(service.spec, mapping)
            su.write()
        mapping.save()
        DAO().save(service,mapping)
        # os.remove("service.pickle")
        sys.stdout.write("success: %e\n" % mapping.objective_function)
        return 0
    else:
        sys.stdout.write("failure\n")
        # mapping = solve(service, su,allow_violations=True)
        # if mapping:
        #    for index, violation in enumerate(mapping.violations,start=1):
        #        print("violation %d : %s" % (index,violation))
        return 1


if __name__ == "__main__":


    parser = argparse.ArgumentParser(description='1 iteration for solver')
    parser.add_argument('-d', "--dry-run", dest='dry', action='store_true')
    parser.add_argument('--vhg', help="the number of failure until the algorithm stops", default=None)
    parser.add_argument('--vcdn', help="number of VCDN", default=None)
    parser.add_argument('--s', help="number of starter", default=1,type=int)
    parser.add_argument('--cdn', help="number of cdn", default=1,type=int)
    parser.add_argument('--reuse', help="Start from a new substrate", dest='reuse', action='store_true')
    parser.add_argument('--grid', help="Start from a new substrate", default=None, type=valid_grid)
    parser.add_argument('--spvhg-disable', help="Disable grouping vhg by shortest path", dest='spvhg_disable',
                        action='store_true')

    parser.add_argument('--vhgpa-disable', help="Disable grouping vhg by shortest path", dest='vhgpa',
                        action='store_true')

    args = parser.parse_args()
    exit(do_step(args.dry,args.spvhg_disable,args.vhgpa,args.reuse,args.grid,args.s,args.cdn,args.vhg,args.vcdn ))



