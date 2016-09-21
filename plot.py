#!/usr/bin/env python


import argparse
import os
import subprocess
import tempfile

from offline.core.service import Service
from offline.time.persistence import Session
from offline.time.plottingDB import plotsol_from_db

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), './offline/results')

parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument('--svg', dest='dosvg', action='store_true')
parser.add_argument('--dest', help="destination for the SVG file", default=os.path.join(RESULTS_FOLDER, "./res.svg"))
parser.add_argument('--service_link_linewidth', default=5, type=int)
parser.add_argument('--net', dest='net', action='store_true', help="print only the network")
parser.add_argument('--view', dest='view', action='store_true')
parser.add_argument("-s", '--serviceid', type=int)

args = parser.parse_args()

# if not args.net:
#     graphiz_exe="neato"
# else:
#     graphiz_exe="dot"

session = Session()
service = session.query(Service).order_by(Service.id.desc()).all()[0]
service_id = str(service.id)
# service.slas[0].substrate.write(path=str(args.serviceid))

dosvg = args.dosvg
plotsol_from_db(service_link_linewidth=args.service_link_linewidth, net=args.net, service=service)
if not dosvg:
    file = tempfile.mkstemp(".pdf")[1]
    subprocess.Popen(
        ["neato", os.path.join(RESULTS_FOLDER, service_id, "./substrate.dot"), "-Tpdf", "-o", file]).wait()
    if args.view:
        subprocess.Popen(["evince", file]).wait()
else:
    file = args.dest
    subprocess.Popen(
        ["neato", os.path.join(RESULTS_FOLDER, service_id, "./substrate.dot"), "-Tsvg", "-o", file]).wait()
    if args.view:
        subprocess.Popen(["eog", file]).wait()
