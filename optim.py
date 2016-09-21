#!/usr/bin/env python

import argparse
import logging
from offline.tools.ostep import create_experiment_and_optimize


def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return (name, spec)
logging.basicConfig(filename='simu.log', level="DEBUG", )

parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument("--just-topo", dest='just_topo', action='store_true')
parser.add_argument('--sla_delay', help="delay toward vCDN", default=30.0, type=float)
parser.add_argument('--start', metavar='S', type=str, nargs='+', help='a list of starters', required=True)
parser.add_argument('--cdn', metavar='CDN', type=str, nargs='+', help='a list of CDN', required=True)

parser.add_argument('--vhg', type=int, help='vhg count', default=None)
parser.add_argument('--vcdn', type=int, help='vcdn count', default=None)
parser.add_argument('--auto', dest='auto', action='store_true', help='automatic vhg vcdn count', default=False)

parser.add_argument('--vcdnratio', help="the share of source traffic toward vcdn", default=0.35, type=float)
parser.add_argument('--sourcebw', help="cumulated source bw from every source", default=100, type=int)
parser.add_argument('--topo', help="specify topo to use", default=('grid', ["5", "5"]), type=valid_topo)

args = parser.parse_args()

if args.auto is False and (args.vhg is None or args.vcdn is None):
    parser.error('please specify --vhg and --vcdn args if not automatic calculation')
elif args.auto is True and (args.vhg is not None or args.vcdn is not None):
    parser.error("can't specify vhg count of vcdn count in --auto mode")

create_experiment_and_optimize(args.start, args.cdn, args.sourcebw, args.topo, 0, vhg_count=args.vhg, vcdn_count=args.vcdn,
                               automatic=args.auto)
