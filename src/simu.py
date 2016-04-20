#!/usr/bin/env python

import argparse
import pickle

from plotting import plot_all_results
from simulation import do_simu

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--threshold', help="the number of failure until the algorithm stops", default=10)
parser.add_argument('--seed', help="integer seed used for random number generation", default=114613154)
parser.add_argument('--count',
                    help="how many simulation to perform. Seed will be increased by 1 each time a new simu is run",
                    default=1)

args = parser.parse_args()

rejected_threshold = int(args.threshold)
sla_count = 10000
init_point = 1
s = int(args.seed)

for seed in range(s, s + int(args.count), 1):
    res = {}
    res["vhg"] = do_simu(True, False, True, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,
                         name="vhg")
    res["none"] = do_simu(False, False, False, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,
                          name="none")

    res["vcdn"] = do_simu(False, True, False, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,
                          name="vcdn")
    res["all"] = do_simu(True, True, False, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,
                         name="all")

    # initial substracte bandwidth capacity
    init_bw = float(res["none"][0].split("\t")[0])
    # initial substrate cpu capacity
    init_cpu = float(res["none"][0].split("\t")[1])

    # do the plotting if pdf files
    plot_all_results(init_bw, init_cpu, res, init_point, seed)

    # save results just in case
    with open("results.pickle", "w") as f:
        pickle.dump(res, f)

# plt.savefig('node-cap.pdf', format='pdf')
