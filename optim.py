#!/usr/bin/env python3

import argparse
import base64
import json
import logging
import os
import shutil
import subprocess
import sys
from argparse import RawTextHelpFormatter

from offline.time.plottingDB import plotsol_from_db
from offline.tools.api import clean_and_create_experiment, optimize_sla, create_sla, generate_sla_nodes

# LOGGING CONFIGURATION
root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stderr)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


def compute_mapping(substrate_topology, start_mapped_nodes, cdn_mapped_nodes, service_bandwidth_demand, vhg_count,
                    vcdn_count, is_automatic_mode, disable_heuristic, seed):
    '''

    :param substrate_topology:
    :param start_mapped_nodes:
    :param cdn_mapped_nodes:
    :param service_bandwidth_demand:
    :param vhg_count:
    :param vcdn_count:
    :param is_automatic_mode:
    :param disable_heuristic:
    :param seed:
    :return: best service and the # of candidates examined
    '''
    # get the random generator and the substrate
    rs, su = clean_and_create_experiment(substrate_topology, seed)

    # generate the mapped nodes according to the stubstrate and the args
    start_nodes, cdn_nodes = generate_sla_nodes(su, start_mapped_nodes, cdn_mapped_nodes, rs)

    # from the mapped node, generate the SLA
    sla = create_sla(start_nodes, cdn_nodes, service_bandwidth_demand, su=su, rs=rs)

    # compute the best mapping
    service, count_embedding = optimize_sla(sla, vhg_count=vhg_count,
                                            vcdn_count=vcdn_count,
                                            automatic=is_automatic_mode, use_heuristic=not disable_heuristic)

    return service, count_embedding


def handle_no_embedding(topo, seed, dest_folder, is_json_requested, is_plot_requested):
    rs, su = clean_and_create_experiment(topo, seed)

    if is_json_requested:  # dumps json to stdout (base64 encoded)
        topo = su.get_json()
        if args.b64:
            sys.stdout.write(base64.b64encode(json.dumps(topo)))
        else:
            sys.stdout.write(json.dumps(topo))
        sys.stdout.flush()

    if is_plot_requested:  # display the plot with external image viewer
        plotsol_from_db(service_link_linewidth=5, net=True, substrate=su)
        subprocess.Popen(
            ["neato", os.path.join(RESULTS_FOLDER, "./substrate.dot"), "-Tsvg", "-o",
             os.path.join(args.dest_folder, "service_graph.svg")]).wait()
        source_path = os.path.normpath(os.path.join(RESULTS_FOLDER, "./substrate.dot"))
        dest_path = os.path.normpath(os.path.join(dest_folder, "substrate.dot"))
        if source_path != dest_path:
            shutil.copy(os.path.join(RESULTS_FOLDER, "./substrate.dot"), )
        subprocess.Popen(["eog", os.path.join(dest_folder, "service_graph.svg")]).wait()


# utility function for params
def unpack(first, *rest):
    return first, rest


def valid_topo(topo_spec):
    name, spec = unpack(*topo_spec.split(","))
    return name, spec


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
parser.add_argument('--sla_delay', help="delay toward TE, float in ms", default=30.0, type=float)
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
parser.add_argument('--topo', help="specify service_graph to use",
                    default=('grid', ["5", "5", "100000000", "10", "200"]),
                    type=valid_topo)

parser.add_argument('--plot', dest="plot", action="store_true")
parser.add_argument('--disable-heuristic', dest="disable_heuristic", action="store_true")
parser.add_argument('--dest_folder', help="destination folder for restults", default=RESULTS_FOLDER)
parser.add_argument('--json', help='display json results in stdout', dest="json", action="store_true")
parser.add_argument('--base64', help='display json results in base64', dest="b64", action="store_true")

args = parser.parse_args()

if args.auto is False and (args.vhg is None or args.vcdn is None):
    parser.error('please specify --vhg and --vcdn args if not automatic calculation')
elif args.auto is True and (args.vhg is not None or args.vcdn is not None):
    parser.error("can't specify vhg count of vcdn count in --auto mode")

# no embedding ==> just senting the topology infos
if args.disable_embedding:
    handle_no_embedding(args.topo, args.seed, args.dest_folder, is_json_requested=args.json,
                        is_plot_requested=args.plot)
else:

    service, count_candidates = compute_mapping(args.topo, args.start, args.cdn, args.sourcebw, args.vhg, args.vcdn,
                                                args.auto,
                                                args.disable_heuristic, args.seed)
    # if a mapping is available
    if service.mapping is not None:
        if args.json:
            output = dict()
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
                f.write("%d,%d\n" % (service.service_graph.get_vhg_count(), service.service_graph.get_vcdn_count()))

            print(("Successfull mapping w price: \t %lf in \t %d embedding \t winner is %d (%d,%d)" % (
                service.mapping.objective_function, count_candidates, service.id, service.service_graph.get_vhg_count(),
                service.service_graph.get_vcdn_count())))

        if args.plot:
            plot_folder = os.path.join(RESULTS_FOLDER, "plot")
            # cleanup plot folder
            if os.path.exists(plot_folder):
                shutil.rmtree(plot_folder)
            os.makedirs(plot_folder)
            print("%s" % plot_folder)

            plotsol_from_db(service_link_linewidth=5, net=False, service=service,
                            dest_folder=plot_folder)
            subprocess.Popen(
                ["neato", os.path.join(plot_folder, "./substrate.dot"), "-Tsvg", "-o",
                 os.path.join(args.dest_folder, "service_graph.svg")]).wait()
            subprocess.Popen(["eog", os.path.join(args.dest_folder, "service_graph.svg")]).wait()

            shutil.copy(os.path.join(plot_folder, "./substrate.dot"), os.path.join(args.dest_folder, "substrate.dot"))
        exit(0)
    else:
        if args.json:
            sys.stdout.write(base64.b64encode(json.dumps({"msg": "failed to compute any mapping"})))
            sys.stdout.flush()
            exit(-1)

        else:
            print("failed to compute mapping")
            exit(-1)
