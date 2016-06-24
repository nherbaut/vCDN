#!/usr/bin/env python

import argparse
import pickle

parser = argparse.ArgumentParser(description='relax your SLA')
parser.add_argument('--vhg', help="the number of failure until the algorithm stops", default=1)
parser.add_argument('--vcdn', help="integer seed used for random number generation", default=1)
args = parser.parse_args()

with open("service.pickle","r") as f:
    service=pickle.load(f)

service.vhgcount = int(args.vhg)
service.vcdncount = int(args.vcdn)

with open("service.pickle","w") as f:
    pickle.dump(service,f)
    service.write()