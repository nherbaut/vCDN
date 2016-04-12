#!/usr/bin/env python

import pickle
import matplotlib.pyplot as plt
import numpy as np
import time
import substrate
from service import Service
from sla import generate_random_slas
from solver import solve
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--threshold',  default=10)
parser.add_argument('--seed',  default=114613154)
parser.add_argument('--count',  default=1)


args = parser.parse_args()


rejected_threshold = int(args.threshold)
sla_count = 10000
s =  int(args.seed)

for seed in range(s, s + int(args.count), 1):

    res = {}


    def do_simu(relax_vhg, relax_vcdn):
        count_transformation = 0
        rs = np.random.RandomState(seed=seed)
        result = []
        rejected = 0
        su = substrate.get_substrate(rs)
        slas = generate_random_slas(rs, su, sla_count)
        f = open("violated-slas.txt", "w")
        g = open("accepted_sla.txt", "w")

        while rejected < rejected_threshold:

            count_transformation_loop=0
            sla = slas.pop()
            service = Service.fromSla(sla)
            mapping = None
            while mapping is None:
                mapping = solve(service, su)

                if mapping is None:
                    if not service.relax(relax_vhg, relax_vcdn):
                        rejected += 1
                        # stdout.write("X")
                        # f.write("%s transformation:%d\n" % (sla,count_transformation))
                        break
                    count_transformation_loop += 1

                else:
                    # stdout.write("O")
                    # g.write("ok! %s transformation:%d\n" % (sla,count_transformation))
                    # print ("ok! %s transformation:%d\n" % (sla,count_transformation))
                    count_transformation+=count_transformation_loop
                    mapping.save()
                    su.consume_service(service, mapping)
                    su.write()
                    #su.write(edges_file="res/%05d-resulting-substrate.edges.data" % (sla_count - len(slas)),                             nodes_file="res/%05d-resulting-substrate.nodes.data" % (sla_count - len(slas)))
                    result.append("%s\t%d\t%d" % (su, sla_count - len(slas)-rejected,count_transformation))

        f.close()
        g.close()
        return result



    res["none"]=[]
    res["vcdn"]=[]
    res["vhg"]=[]
    res["all"]=[]
    start=time.time()
    res["none"] = do_simu(False, False)
    print "s0 in %lf for %d run : %lf" % ((time.time()-start),len(res["none"]),(time.time()-start)/(1+len(res["none"])) )
    start=time.time()
    res["vhg"] = do_simu(True, False)
    print "s1 in %lf for %d run : %lf" % ((time.time()-start),len(res["vhg"]),(time.time()-start)/(1+len(res["vhg"])))
    start=time.time()
    res["vcdn"] = do_simu(False, True)
    print "s2 in %lf for %d run : %lf" % ((time.time()-start),len(res["vcdn"]),(time.time()-start)/(1+len(res["vcdn"])))
    start=time.time()
    res["all"] = do_simu(True, True)
    print "s3 in %lf for %d run : %lf" % ((time.time()-start),len(res["all"]),(time.time()-start)/(1+len(res["all"])))

    init_bw = float(res["none"][0].split("\t")[0])
    init_cpu = float(res["none"][0].split("\t")[1])

    init_point = 0

    plt.figure(0)
    none = plt.plot([float(x.split("\t")[2]) for x in res["none"]][init_point:],
                    [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["none"]][init_point:],
                    'r', label="none",
                    linestyle="solid")

    vhg = plt.plot([float(x.split("\t")[2]) for x in res["vhg"]][init_point:],
                   [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["vhg"]][init_point:],
                   'b', label="vhg",
                   linestyle="solid")
    vcdn = plt.plot([float(x.split("\t")[2]) for x in res["vcdn"]][init_point:],
                    [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["vcdn"]][init_point:],
                    'y', label="vcdn",
                    linestyle="solid")
    all = plt.plot([float(x.split("\t")[2]) for x in res["all"]][init_point:],
                   [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["all"]][init_point:],
                   'g', label="all",
                   linestyle="solid")

    plt.legend(["Canonical", "vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    plt.ylabel('% of Substrate Bandwidth Usage')
    plt.xlabel('# of Embeded SLA')
    # plt.show()
    plt.savefig("edge-capacities%d.pdf" % seed, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)

    plt.clf()
    plt.figure(1)


    none = plt.plot([float(x.split("\t")[2]) for x in res["none"]][init_point:],
                    [100 - float(x.split("\t")[1])/ init_cpu * 100  for x in res["none"]][init_point:],
                    'r', label="none",
                    linestyle="solid")

    vhg = plt.plot([float(x.split("\t")[2]) for x in res["vhg"]][init_point:],
                   [100 - float(x.split("\t")[1])/ init_cpu * 100  for x in res["vhg"]][init_point:],
                   'b', label="vhg",
                   linestyle="solid")

    vcdn = plt.plot([float(x.split("\t")[2]) for x in res["vcdn"]][init_point:],
                    [100 - float(x.split("\t")[1])/ init_cpu * 100 for x in res["vcdn"]][init_point:],
                    'y', label="vcdn",
                    linestyle="solid")
    all = plt.plot([float(x.split("\t")[2]) for x in res["all"]][init_point:],
                   [100 - float(x.split("\t")[1])/ init_cpu * 100 for x in res["all"]][init_point:],
                   'g', label="all",
                   linestyle="solid")

    plt.legend(["Canonical", "vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
    plt.ylabel('% of Substrate Node Capacity Usage')
    plt.xlabel('# of Embeded SLA')
    # plt.show()


    plt.savefig("node-capacities%d.pdf" % seed, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)
    plt.clf()
    plt.figure(2)






    vhg = plt.plot([float(x.split("\t")[2]) for x in res["vhg"]][init_point:],
                   [float(x.split("\t")[3]) for x in res["vhg"]][init_point:],
                   'b', label="vhg",
                   linestyle="solid")

    vcdn = plt.plot([float(x.split("\t")[2]) for x in res["vcdn"]][init_point:],
                    [float(x.split("\t")[3])  for x in res["vcdn"]][init_point:],
                    'y', label="vcdn",
                    linestyle="solid")
    all = plt.plot([float(x.split("\t")[2]) for x in res["all"]][init_point:],
                   [float(x.split("\t")[3])  for x in res["all"]][init_point:],
                   'g', label="all",
                   linestyle="solid")


    plt.ylabel("# for transformation required by embedding")
    plt.xlabel('# of Embeded SLA')
    plt.legend(["vHG", "vCDN", "vHG+vCDN"], bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)

    plt.savefig("transfo%d.pdf" % seed, dpi=None, facecolor='w', edgecolor='w',
                orientation='landscape', papertype="A4", format="pdf",
                transparent=False, bbox_inches=None, pad_inches=0.1,
                frameon=None)

    with open("results.pickle","w") as f:
        pickle.dump(res,f)

# plt.savefig('node-cap.pdf', format='pdf')
