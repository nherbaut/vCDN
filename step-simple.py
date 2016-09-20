#!/usr/bin/env python

import argparse
from offline.tools.ostep import create_experiment_and_optimize

def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return (name, spec)


parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument("--just-topo", dest='just_topo', action='store_true')
parser.add_argument('--sla_delay', help="delay toward vCDN", default=30.0, type=float)
parser.add_argument('--start', metavar='S', type=str, nargs='+',default=["0101"],
                    help='a list of starters')
parser.add_argument('--cdn', metavar='CDN', type=str, nargs='+',default=["0505"],
                    help='a list of CDN')

parser.add_argument('--vcdnratio', help="the share of source traffic toward vcdn", default=0.35, type=float)
parser.add_argument('--sourcebw', help="cumulated source bw from every source", default=100, type=int)
parser.add_argument('--topo', help="specify topo to use", default=('grid', ["5", "5"]), type=valid_topo)

args=parser.parse_args()


create_experiment_and_optimize(args.start,args.cdn,args.sourcebw,args.topo,0)