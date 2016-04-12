#!/usr/bin/env python
import argparse

parser = argparse.ArgumentParser(description='generate service')
parser.add_argument('--vhgcpu', type=float, default=60.0)
parser.add_argument('--vhgcpuR', type=float, default=100.0)

parser.add_argument('--vhgdelay', type=float, default=6.0325871714 + 2 * 4.7468491485)
parser.add_argument('--vhgdelayR', type=float, default=100)

parser.add_argument('--cdndelay', type=float, default=6.0325871714 + 20 * 4.7468491485)
parser.add_argument('--cdndelayR', type=float, default=100)

parser.add_argument('--vcdndelay', type=float, default=6.0325871714 + 4 * 4.7468491485)
parser.add_argument('--vcdndelayR', type=float, default=100)

parser.add_argument('--vcdncpu', type=float, default=30.0)
parser.add_argument('--vcdncpuR', type=float, default=100.0)

parser.add_argument('--vhgcount', type=int, default=1)
parser.add_argument('--vcdncount', type=int, default=1)

parser.add_argument('--sourcebw', type=float, default=7875857142.85714 / 5.0)
parser.add_argument('--sourcebwR', type=float, default=100.0)

parser.add_argument('--vcdnratio', type=float, default=0.35)

args = parser.parse_args()

sourcebw = float(args.sourcebw) / float(args.sourcebwR) * 100
vhgcount = float(args.vhgcount)
vhgdelay = args.vhgdelay / float(args.vhgdelayR) * 100
vhgcount = args.vhgcount
vcdnratio = args.vcdnratio
cdndelay = args.cdndelay / float(args.cdndelayR) * 100
vcdndelay = args.vcdndelay / float(args.vcdndelayR) * 100
sourcebw = args.sourcebw
vcdncpu = args.vcdncpu / float(args.vcdncpuR) * 100
vhgcpu = args.vhgcpu / float(args.vhgcpuR) * 100
vcdncount = args.vcdncount

# print ( "sourcebw=%lf vhgcount=%lf vhgdelay=%lf  vhgcount=%lf  vcdnratio=%lf cdndelay=%lf vcdndelay=%lf sourcebw=%lf vcdncpu=%lf vhgcpu=%lf vcdncount=%lf"%(sourcebw,vhgcount,vhgdelay,vhgcount,vcdnratio,cdndelay,vcdndelay,sourcebw,vcdncpu,vhgcpu,vcdncount,))


with open("service.edges.data", "w") as f:
    f.write("S	LB	%ld	5\n" % sourcebw)
    for i in range(1, int(vhgcount) + 1):
        f.write("LB	VHG%d	%lf	%lf\n" % (i, sourcebw / vhgcount, vhgdelay))
        f.write("VHG%d	CDN %lf	%lf\n" % (i, sourcebw / vhgcount * (1 - vcdnratio), cdndelay))
        for j in range(1, int(vcdncount) + 1):
            f.write("VHG%d	vCDN%d %lf	%lf\n" % (i, j,
                                                      sourcebw / (vhgcount * vcdncount) * vcdnratio,
                                                      vcdndelay))

with open("service.nodes.data", "w") as f:
    f.write("S	0	\n")
    f.write("LB	0	\n")
    f.write("CDN	0	\n")
    for j in range(1, int(vcdncount) + 1):
        f.write("vCDN%d	%lf	\n" % (j, vcdncpu / vcdncount))

    for i in range(1, int(vhgcount) + 1):
        f.write("VHG%d %lf\n" % (i, vhgcpu / vhgcount))
