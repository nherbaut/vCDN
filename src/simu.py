#!/usr/bin/env python

import argparse
import os.path
import pickle
import random
import sys

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

    #res["none"] = do_simu(False, False,  seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,                          name="none",iteration_threshold=iteration_threshold)
    #res["vcdn"] = do_simu(False, True,  seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,                          name="vcdn",iteration_threshold=iteration_threshold)
    #res["vhg.4"] = do_simu(True, False,  seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,                         name="VHG-PAPER4",iteration_threshold=iteration_threshold,preassign_vhg=True)
    res["all.4"] = do_simu(relax_vhg=True, relax_vcdn=True,  seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,                         name="VHG+VCDN-PAPER4",iteration_threshold=iteration_threshold,
                           smart_ass=True)
    #res["vhg.3"] = do_simu(True, False,  seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,                         name="VHG-PAPER3",iteration_threshold=iteration_threshold,preassign_vhg=False)
    #res["all.3"] = do_simu(True, True,  seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,                         name="VHG+VCDN-PAPER3",iteration_threshold=iteration_threshold,preassign_vhg=False)
    #res["baseline"] = do_simu(False,  False, seed=seed, sla_count=sla_count, rejected_threshold=rejected_threshold,                         name="baseline",iteration_threshold=iteration_threshold,preassign_vhg=False)


    if os.path.isfile("results.pickle"):
        with open("results.pickle", "r") as f:
            res_file=pickle.load(f)
    else:
        res_file={}



    for key in res.keys():
        if key in res_file:


            print "won't add %s to already existing result" % key
            new_key=key + str(random.uniform(1,10000))
            print "writing to another result instead : %s" % new_key
            res_file[new_key]=res[key]
        else:
            res_file[key]=res[key]



    # save results just in case
    with open("results.pickle", "w") as f:
        pickle.dump(res_file, f)


    print("saved results with keys:")
    for key in res.keys():
        if key in res_file:
            sys.stdout.write("%s "%key)

    sys.stdout.write("\n")

    # do the plotting if pdf files
    #plot_all_results(res, init_point, seed)



# plt.savefig('node-cap.pdf', format='pdf')
