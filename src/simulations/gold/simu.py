#!/usr/bin/env python


from sys import stdout

import numpy as np

import substrate
from service import Service
from sla import generate_random_slas
from solver import solve

rejected_threshold = 10
sla_count = 10000
rejected = 0
rs = np.random.RandomState(seed=13461348)
su = substrate.get_substrate(rs)
slas = generate_random_slas(rs, su, sla_count)
f = open("violated-slas.txt", "w")
g = open("accepted_sla.txt", "w")

while rejected < rejected_threshold:
    count_transformation=0
    sla = slas.pop()
    service = Service.fromSla(sla)
    mapping = None
    while mapping == None:
        mapping = solve(service, su)
        if mapping == None:
            if  service.relax() == False:
                rejected = rejected + 1
                stdout.write("X")
                f.write("%s transformation:%d\n" % (sla,count_transformation))
                break
            count_transformation=count_transformation+1

        else:
            stdout.write("O")
            #g.write("ok! %s transformation:%d\n" % (sla,count_transformation))
            print ("ok! %s transformation:%d\n" % (sla,count_transformation))
            su.consume_service(service, mapping)

print "\n%s %d" % (su, sla_count - len(slas))
f.close()
g.close()
