#!/usr/bin/env python

import argparse
import logging
import os
import subprocess
from argparse import RawTextHelpFormatter

from offline.time.plottingDB import plotsol_from_db
from offline.tools.ostep import create_sla, clean_and_create_experiment, optimize_sla
import shutil

def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return (name, spec)


RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'offline/results')

logging.basicConfig(filename='simu.log', level="DEBUG", )

parser = argparse.ArgumentParser(description='1 iteration for solver', epilog=

""" Examples for different topologies:
    \t sudo docker run nherbaut/simuservice --start 0101 0202 0303 --cdn 0505 --vhg 1 --vcdn 1  --topo=powerlaw,n, m, p, seed, bw, delay, cpu\n
    \t sudo docker run nherbaut/simuservice --start 1 2 3 --cdn 93 --vhg 1 --vcdn 1 --topo=powerlaw,100,2,0.3,1,1000000000,20,200\n\n\n
    \t sudo docker run nherbaut/simuservice --start 0101 0202 0303 --cdn 0505 --vhg 1 --vcdn 1  --topo=erdos_renyi,n, p, seed, bw, delay, cpu\n
    \t sudo docker run nherbaut/simuservice --start 1 2 3 --cdn 10 --vhg 1 --vcdn 1 --topo=erdos_renyi,20,0.3,1,1000000000,20,200\n\n\n
    \t sudo docker run nherbaut/simuservice --start 0101 0202 0303 --cdn 0505 --vhg 1 --vcdn 1  --topo=grid,width, height, bw, delay, cpu\n
    \t sudo docker run nherbaut/simuservice --start 0101 0202 0303 --cdn 0505 --vhg 1 --vcdn 1 --topo=grid,5,5,1000000000,10,1000\n\n\n
    \t sudo docker run nherbaut/simuservice --start 22  --cdn 38 --vhg 1 --vcdn 1 --topo=file,file,cpu\n
    \t sudo docker run nherbaut/simuservice --start 22  --cdn 38 --vhg 1 --vcdn 1 --topo=file,Geant2012.graphml,10000


    """, formatter_class=RawTextHelpFormatter)
parser.add_argument("--disable-embedding", dest='disable_embedding',
                    help="disable the embedding, which cause the topology to be rendrered alone", action='store_true')
parser.add_argument('--sla_delay', help="delay toward vCDN, float in ms", default=30.0, type=float)
parser.add_argument('--start', metavar='S', type=str, nargs='+', help='a list of starters (eg. 0101 0202 0304)',
                    required=True)
parser.add_argument('--cdn', metavar='CDN', type=str, nargs='+', help='a list of CDN (eg. 0505)', required=True)

parser.add_argument('--vhg', type=int, help='vhg count (eg. 2)', default=None)
parser.add_argument('--vcdn', type=int, help='vcdn count (eg. 1)', default=None)
parser.add_argument('--auto', dest='auto', action='store_true', help='automatic vhg vcdn count', default=False)

parser.add_argument('--vcdnratio', help="the share of source traffic toward vcdn (default 0.35)", default=0.35,
                    type=float)
parser.add_argument('--sourcebw', help="cumulated source bw from every source (default 100 bits) ", default=10000,
                    type=float)
parser.add_argument('--topo', help="specify topo to use", default=('grid', ["5", "5", "100000000", "10", "200"]),
                    type=valid_topo)

parser.add_argument('--plot', dest="plot", action="store_true")
parser.add_argument('--disable-heuristic', dest="disable_heuristic", action="store_true")
parser.add_argument('--dest_folder', help="destination folder for restults", default=RESULTS_FOLDER)

args = parser.parse_args()

if args.disable_embedding:
    rs, su = clean_and_create_experiment(args.topo, 0)

    su.write(RESULTS_FOLDER)
    plotsol_from_db(service_link_linewidth=5, net=True, substrate=su)
    subprocess.Popen(
        ["neato", os.path.join(RESULTS_FOLDER, "./substrate.dot"), "-Tsvg", "-o",
         os.path.join(args.dest_folder, "topo.svg")]).wait()


else:

    if args.auto is False and (args.vhg is None or args.vcdn is None):
        parser.error('please specify --vhg and --vcdn args if not automatic calculation')
    elif args.auto is True and (args.vhg is not None or args.vcdn is not None):
        parser.error("can't specify vhg count of vcdn count in --auto mode")

    sla = create_sla(args.start, args.cdn, args.sourcebw, args.topo, 0)
    service, count_embedding = optimize_sla(sla,vhg_count=args.vhg,
                                            vcdn_count=args.vcdn,
                                            automatic=args.auto, use_heuristic=not args.disable_heuristic)

    if os.path.exists("winner"):
        shutil.rmtree("winner")
    shutil.copytree(os.path.join(RESULTS_FOLDER,str(service.id)),"winner")

    if service.mapping is not None:
        with     open(os.path.join(args.dest_folder, "price.data"), "w") as f:
            f.write("%lf\n" % service.mapping.objective_function)
            f.write("%d,%d\n" % (service.vhg_count,service.vcdn_count))
            dest_folder = os.path.join(RESULTS_FOLDER, str(service.id))
            plotsol_from_db(service_link_linewidth=5, net=False, service=service,
            dest_folder = dest_folder)

            print("Successfull mapping w price: \t %lf in \t %d embedding \t winner is %d" % (service.mapping.objective_function, count_embedding,service.id))
            subprocess.Popen(
        ["neato", os.path.join(dest_folder, "./substrate.dot"), "-Tsvg", "-o",
         os.path.join(args.dest_folder, "topo.svg")]).wait()
    else:
        print("failed to compute mapping")
