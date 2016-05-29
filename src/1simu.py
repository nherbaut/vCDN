#!/usr/bin/env python
import logging
logging.basicConfig(filename='simu.log',level=logging.DEBUG)


import argparse
import pickle
import sys
import random
from plotting import plot_all_results
from simulation import do_simu
import os.path
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--threshold', help="the number of failure until the algorithm stops", default=0)
parser.add_argument('--ithreshold', help="the number of run of the algo", default=0)

parser.add_argument('--seed', help="integer seed used for random number generation", default=114613154)
parser.add_argument('--relaxVhg', help="boolean expression that allow the algo to add VHG", dest='relaxVhg', action='store_true')
parser.add_argument('--relaxvCDN', help="boolean expression that allow the algo to add vCDN", dest='relaxvCDN', action='store_true')
parser.add_argument('--name', help="name of the experiment", default="unamed experiment")
parser.add_argument('--smart-disable', dest='smart_ass', action='store_false')
parser.add_argument('--unsorted-sla', dest='unsorted_sla', action='store_true')
parser.add_argument('--cpuCost', help="unit cost of the cpu",default=1000)
parser.add_argument('--netCost', help="unit cost of the networking",default=20000)






args = parser.parse_args()

rejected_threshold = int(args.threshold)
iteration_threshold= int(args.ithreshold)
sla_count = 10000
init_point = 0
s = int(args.seed)
seed=int(args.seed)
res={}
relax_vhg=args.relaxVhg
relax_vcdn=args.relaxvCDN
smart_ass=args.smart_ass
sorted_sla=(args.unsorted_sla is True)

res[args.name] = do_simu(relax_vhg=relax_vhg,
                       relax_vcdn=relax_vcdn,
                       seed=seed,
                       sla_count=sla_count,
                       rejected_threshold=rejected_threshold,
                       name=args.name,
                       iteration_threshold=iteration_threshold,
                       smart_ass=smart_ass,
                       cpuCost=int(args.cpuCost),
                       netCost=float(args.netCost)/10.0**9,
                       sorted=sorted_sla
                        )


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
