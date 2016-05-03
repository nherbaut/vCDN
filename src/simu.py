#!/usr/bin/env python

import argparse
import pickle

from plotting import plot_all_results
from simulation import do_simu

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--threshold', help="the number of failure until the algorithm stops", default=0)
parser.add_argument('--ithreshold', help="the number of run of the algo", default=0)

parser.add_argument('--seed', help="integer seed used for random number generation", default=114613154)
parser.add_argument('--count',
                    help="how many simulation to perform. Seed will be increased by 1 each time a new simu is run",
                    default=1)

args = parser.parse_args()

rejected_threshold = int(args.threshold)
iteration_threshold= int(args.ithreshold)
sla_count = 10000
init_point = 0
s = int(args.seed)

for seed in range(s, s + int(args.count), 1):
    res = {}

    res["none"] = do_simu(False, False, False, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,
                          name="none",iteration_threshold=iteration_threshold)
    res["vcdn"] = do_simu(False, True, False, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,
                          name="vcdn",iteration_threshold=iteration_threshold)
    res["vhg"] = do_simu(True, False, False, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,
                         name="vhg",iteration_threshold=iteration_threshold)


    res["all"] = do_simu(True, True, False, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,
                         name="all",iteration_threshold=iteration_threshold)


      # save results just in case
    with open("results.pickle", "w") as f:
        pickle.dump(res, f)


    # do the plotting if pdf files
    plot_all_results(res, init_point, seed)



# plt.savefig('node-cap.pdf', format='pdf')
