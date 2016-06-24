#!/usr/bin/env python
import pickle
from plotting import plot_all_results
import sys

import argparse

parser = argparse.ArgumentParser(description='Display graphs from stored results')

parser.add_argument('--min', help="when to start drawing", default=0,type=int)
parser.add_argument('--max', help="when to stop drawing", default=sys.maxint,type=int)
args = parser.parse_args()




with open("results.pickle", "r") as f:
        res=pickle.load(f)

sys.stdout.write("generating graphs for:\n")
for key in res.keys():
    sys.stdout.write("\t-%s\n"%key)
plot_all_results(res, args.min,args.max, 0 )
sys.stdout.write("done\n")