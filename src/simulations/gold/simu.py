#!/usr/bin/env python


import matplotlib.pyplot as plt
import numpy as np

import substrate
from service import Service
from sla import generate_random_slas
from solver import solve

rejected_threshold = 150
sla_count = 10000
s = 114613154

for seed in range(s, s + 5, 1):

    res = {}


    def do_simu(relax_vhg, relax_vcdn):
        rs = np.random.RandomState(seed=seed)
        result = []
        rejected = 0
        su = substrate.get_substrate(rs)
        slas = generate_random_slas(rs, su, sla_count)
        f = open("violated-slas.txt", "w")
        g = open("accepted_sla.txt", "w")

        while rejected < rejected_threshold:
            result.append("%s\t%d" % (su, sla_count - len(slas)))
            count_transformation = 0
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
                    count_transformation += 1

                else:
                    # stdout.write("O")
                    # g.write("ok! %s transformation:%d\n" % (sla,count_transformation))
                    # print ("ok! %s transformation:%d\n" % (sla,count_transformation))
                    mapping.save()
                    su.consume_service(service, mapping)
                    su.write(edges_file="res/%05d-resulting-substrate.edges.data" % (sla_count - len(slas)),
                             nodes_file="res/%05d-resulting-substrate.nodes.data" % (sla_count - len(slas)))

        f.close()
        g.close()
        return result


    res["none"] = do_simu(False, False)
    res["vhg"] = do_simu(True, False)
    res["vcdn"] = do_simu(False, True)
    res["all"] = do_simu(True, True)

    init_bw = float(res["none"][0].split("\t")[0])
    init_cpu = float(res["none"][0].split("\t")[1])

    init_point = 100

    plt.figure(0)
    none = plt.plot([float(x.split("\t")[2]) for x in res["none"]][init_point:],
                    [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["none"]][init_point:],
                    'r.', label="none",
                    linestyle="solid")

    vhg = plt.plot([float(x.split("\t")[2]) for x in res["vhg"]][init_point:],
                   [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["vhg"]][init_point:],
                   'b.', label="vhg",
                   linestyle="solid")
    vcdn = plt.plot([float(x.split("\t")[2]) for x in res["vcdn"]][init_point:],
                    [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["vcdn"]][init_point:],
                    'y.', label="vcdn",
                    linestyle="solid")
    all = plt.plot([float(x.split("\t")[2]) for x in res["all"]][init_point:],
                   [100 - float(x.split("\t")[0]) / init_bw * 100 for x in res["all"]][init_point:],
                   'g.', label="all",
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
                    [100 - float(x.split("\t")[1]) / init_cpu * 100 for x in res["none"]][init_point:],
                    'r.', label="none",
                    linestyle="solid")

    vhg = plt.plot([float(x.split("\t")[2]) for x in res["vhg"]][init_point:],
                   [100 - float(x.split("\t")[1]) / init_cpu * 100 for x in res["vhg"]][init_point:],
                   'b.', label="vhg",
                   linestyle="solid")

    vcdn = plt.plot([float(x.split("\t")[2]) for x in res["vcdn"]][init_point:],
                    [100 - float(x.split("\t")[1]) / init_cpu * 100 for x in res["vcdn"]][init_point:],
                    'y.', label="vcdn",
                    linestyle="solid")
    all = plt.plot([float(x.split("\t")[2]) for x in res["all"]][init_point:],
                   [100 - float(x.split("\t")[1]) / init_cpu * 100 for x in res["all"]][init_point:],
                   'g.', label="all",
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
# plt.savefig('node-cap.pdf', format='pdf')
