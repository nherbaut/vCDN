#!/usr/bin/env python

import argparse
import base64
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from argparse import RawTextHelpFormatter

import offline.core.sla
from offline.time.plottingDB import plotsol_from_db
from offline.tools.ostep import clean_and_create_experiment, optimize_sla, create_sla

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stderr)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


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
                    )
parser.add_argument('--cdn', metavar='CDN', type=str, nargs='+', help='a list of CDN (eg. 0505)', )

parser.add_argument('--vhg', type=int, help='vhg count (eg. 2)', default=None)
parser.add_argument('--seed', type=int, help='seed for random number generation', default=1)
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
parser.add_argument('--json', help='display json results in stdout', dest="json", action="store_true")
parser.add_argument('--base64', help='display json results in base64', dest="b64", action="store_true")

args = parser.parse_args()

if args.disable_embedding:
    rs, su = clean_and_create_experiment(args.topo, 0)

    su.write(RESULTS_FOLDER)
    if args.json:
        topo = su.get_json()
        if args.b64:
            sys.stdout.write(base64.b64encode(json.dumps(topo)))
        else:
            sys.stdout.write(json.dumps(topo))
        sys.stdout.flush()
    if args.plot:
        plotsol_from_db(service_link_linewidth=5, net=True, substrate=su)
        subprocess.Popen(
            ["neato", os.path.join(RESULTS_FOLDER, "./substrate.dot"), "-Tsvg", "-o",
             os.path.join(args.dest_folder, "topo.svg")]).wait()
        source_path = os.path.normpath(os.path.join(RESULTS_FOLDER, "./substrate.dot"))
        dest_path = os.path.normpath(os.path.join(args.dest_folder, "substrate.dot"))
        if source_path != dest_path:
            shutil.copy(os.path.join(RESULTS_FOLDER, "./substrate.dot"), )
        subprocess.Popen(["eog", os.path.join(args.dest_folder, "topo.svg")]).wait()




else:

    if args.auto is False and (args.vhg is None or args.vcdn is None):
        parser.error('please specify --vhg and --vcdn args if not automatic calculation')
    elif args.auto is True and (args.vhg is not None or args.vcdn is not None):
        parser.error("can't specify vhg count of vcdn count in --auto mode")

    rs, su = clean_and_create_experiment(args.topo, args.seed)

    start_nodes = None
    if len(args.start) == 1:
        match = re.findall("RAND\(([0-9]+),([0-9]+)\)", args.start[0])
        if len(match) == 1:
            nodes_by_bw = su.get_nodes_by_bw()
            start_nodes = offline.core.sla.weighted_shuffle(list(nodes_by_bw.keys()), list(nodes_by_bw.values()), rs)[
                          -rs.randint(int(match[0][0]), int(match[0][1]) + 1):]
            logging.debug("random start nodes: %s" % " ".join(start_nodes))

    cdn_nodes = None
    if len(args.cdn) == 1:
        match = re.findall("RAND\(([0-9]+),([0-9]+)\)", args.cdn[0])
        if len(match) == 1:
            nodes_by_degree = su.get_nodes_by_degree()

            cdn_nodes = offline.core.sla.weighted_shuffle(list(nodes_by_degree.keys()), [30-i for i in list(nodes_by_degree.values())], rs)[
                        :rs.randint(int(match[0][0]), int(match[0][1]) + 1)]
            logging.debug("random cdn nodes: %s" % " ".join(cdn_nodes))

    if start_nodes is None:
        start_nodes = args.start

    if cdn_nodes is None:
        cdn_nodes = args.cdn

    sla = create_sla(start_nodes, cdn_nodes, args.sourcebw, su=su, rs=rs)
    service, count_embedding = optimize_sla(sla, vhg_count=args.vhg,
                                            vcdn_count=args.vcdn,
                                            automatic=args.auto, use_heuristic=not args.disable_heuristic)

    if os.path.exists("winner"):
        shutil.rmtree("winner")
    shutil.copytree(os.path.join(RESULTS_FOLDER, str(service.id)), "winner")

    if service.mapping is not None:

        if args.json:
            output = {}
            output["price"] = {'total_price': service.mapping.objective_function, "vhg_count": service.vhg_count,
                               "vcdn_count": service.vcdn_count}
            output["mapping"] = service.mapping.to_json()
            if args.b64:
                sys.stdout.write(base64.b64encode(json.dumps(output)))
            else:
                sys.stdout.write(json.dumps(output))

            sys.stdout.flush()

        else:
            with open(os.path.join(args.dest_folder, "price.data"), "w") as f:
                f.write("%lf\n" % service.mapping.objective_function)
                f.write("%d,%d\n" % (service.vhg_count, service.vcdn_count))

            print(("Successfull mapping w price: \t %lf in \t %d embedding \t winner is %d (%d,%d)" % (
                service.mapping.objective_function, count_embedding, service.id, service.vhg_count, service.vcdn_count)))

        if args.plot:
            dest_folder = os.path.join(RESULTS_FOLDER, str(service.id))
            plotsol_from_db(service_link_linewidth=5, net=False, service=service,
                            dest_folder=dest_folder)
            subprocess.Popen(
                ["neato", os.path.join(dest_folder, "./substrate.dot"), "-Tsvg", "-o",
                 os.path.join(args.dest_folder, "topo.svg")]).wait()
            subprocess.Popen(["eog", os.path.join(args.dest_folder, "topo.svg")]).wait()

            shutil.copy(os.path.join(dest_folder, "./substrate.dot"), os.path.join(args.dest_folder, "substrate.dot"))
        exit(0)


    else:
        if args.json:
            sys.stdout.write(base64.b64encode(json.dumps({"msg": "failed to compute any mapping"})))
            sys.stdout.flush()
            exit(-1)

        else:
            print("failed to compute mapping")
            exit(-1)
