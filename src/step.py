#!/usr/bin/env python

import os
import pickle
import sys
import argparse
import numpy as np
from service import Service
from sla import generate_random_slas
from solver import solve
from substrate import Substrate


parser = argparse.ArgumentParser(description='1 iteration for solver')
parser.add_argument('-d',"--dry-run", dest='dry', action='store_true')
args=parser.parse_args()
dry=args.dry

rs = np.random.RandomState()
su = Substrate.fromFile()




if dry and not os.path.isfile("service.pickle"):
    print("must have a service.pickle to dry-run")
    exit(1)

elif dry:
    with open("service.pickle", "r") as f:
        service = pickle.load(f)
else:
    sla = generate_random_slas(rs, su, 1)[0]
    service = Service.fromSla(sla)
    with open("service.pickle", "w") as f:
        pickle.dump(service, f)



mapping = solve(service, su)

if not mapping is None:
    if not dry:
      su.consume_service(service, mapping)
      su.write()
      mapping.save()
      os.remove("service.pickle")
    sys.stdout.write("success\n")
    exit(0)
else:
    sys.stdout.write("failure\n")
    mapping = solve(service, su,allow_violations=True)
    for index, violation in enumerate(mapping.violations,start=1):
        print("violation %d : %s" % (index,violation))
    exit(1)
