#!/usr/bin/env python
import pickle
from plotting import plot_all_results
import sys
with open("results.pickle", "r") as f:
        res=pickle.load(f)

sys.stdout.write("generating graphs for:\n")
for key in res.keys():
    sys.stdout.write("\t-%s\n"%key)
plot_all_results(res, 0, 0 )
sys.stdout.write("done\n")