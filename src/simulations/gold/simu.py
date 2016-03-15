#!/usr/bin/env python


from sys import stdout
import matplotlib.pyplot as plt
import numpy as np

import substrate
from service import Service
from sla import generate_random_slas
from solver import solve


rejected_threshold = 1000
sla_count = 100000
seed=114613149
res={}




def do_simu(relax_vhg,relax_vcdn):

    rs = np.random.RandomState(seed=seed)
    res=[]
    rejected = 0
    su = substrate.get_substrate(rs)
    slas = generate_random_slas(rs, su, sla_count)
    f = open("violated-slas.txt", "w")
    g = open("accepted_sla.txt", "w")


    while rejected < rejected_threshold:
        res.append( "%s\t%d" % (su, sla_count - len(slas)))
        count_transformation=0
        sla = slas.pop()
        service = Service.fromSla(sla)
        mapping = None
        while mapping == None:
            mapping = solve(service, su)
            if mapping == None:
                if   service.relax(relax_vhg,relax_vcdn) == False:
                    rejected = rejected + 1
                    #stdout.write("X")
                    #f.write("%s transformation:%d\n" % (sla,count_transformation))
                    break
                count_transformation=count_transformation+1

            else:
                #stdout.write("O")
                #g.write("ok! %s transformation:%d\n" % (sla,count_transformation))
                #print ("ok! %s transformation:%d\n" % (sla,count_transformation))
                su.consume_service(service, mapping)
                su.write(edges_file="res/%05d-resulting-substrate.edges.data"%(sla_count-len(slas)),nodes_file="res/%05d-resulting-substrate.nodes.data"%(sla_count-len(slas)))



    f.close()
    g.close()
    return res

res["none"]=do_simu(False,False)
res["vhg"]=do_simu(True,False)
res["vcdn"]=do_simu(False,True)
res["all"]=do_simu(True,True)



none=plt.plot([x.split("\t")[2] for x in res["none"]], [x.split("\t")[0] for x in res["none"]],'r.',label="none")
all=plt.plot([x.split("\t")[2] for x in res["all"]], [x.split("\t")[0] for x in res["all"]],'g.',label="all")
vhg=plt.plot([x.split("\t")[2] for x in res["vhg"]], [x.split("\t")[0] for x in res["vhg"]],'b.',label="vhg")
vcdn=plt.plot([x.split("\t")[2] for x in res["vcdn"]], [x.split("\t")[0] for x in res["vcdn"]],'y.',label="vcdn")

plt.legend(["none", "all","vhg","vcdn"])
plt.show()