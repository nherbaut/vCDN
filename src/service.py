import sys


class Node:
    def __init__(self, cpu):
        self.cpu = cpu


class Edge:
    def __init__(self, bw, delay):
        self.bw = bw
        self.delay = delay


class Service:
    @classmethod
    def fromSla(cls, sla):
        return cls(sourcebw=sla.bandwidth,
                   vhgcount=1,
                   vhgdelay=1 * sla.delay / 4.0,
                   vcdnratio=0.35,
                   cdndelay=sla.delay * 100,
                   vcdndelay=3 * sla.delay / 4.0,
                   vcdncpu=10,
                   vhgcpu=10,
                   vcdncount=1,
                   start=sla.start,
                   cdn=sla.cdn,
                   max_cdn_to_use=sla.max_cdn_to_use)

    def __init__(self, sourcebw, vhgcount, vhgdelay, vcdnratio, cdndelay, vcdndelay, vcdncpu, vhgcpu, vcdncount, start,
                 cdn, max_cdn_to_use):
        self.sourcebw = sourcebw
        self.vhgcount = vhgcount
        self.vhgdelay = vhgdelay
        self.vhgcount = vhgcount
        self.vcdnratio = vcdnratio
        self.cdndelay = cdndelay
        self.vcdndelay = vcdndelay
        self.vcdncpu = vcdncpu
        self.vhgcpu = vhgcpu
        self.vcdncount = vcdncount
        self.start = start
        self.cdn = cdn
        self.nodes = {}
        self.edges = {}
        self.max_cdn_to_use = max_cdn_to_use

    def relax(self, relax_vhg=True, relax_vcdn=True):
        print("relaxation level\t%e " % (self.vhgcount + self.vcdncount - 2))
        if relax_vhg and relax_vcdn:
            if (self.vcdncount + self.vhgcount) % 2 == 0:
                self.vhgcount = self.vhgcount + 1
            else:
                self.vcdncount = self.vcdncount + 1

        elif relax_vhg:
            self.vhgcount = self.vhgcount + 1
        elif relax_vcdn:
            self.vcdncount = self.vcdncount + 1
        else:
            return False  # norelax

        # overrun
        if self.vcdncount > 4 or self.vhgcount > 4:
            return False
        else:
            return True

    def write(self):

        with open("service.edges.data", "w") as f:
            for index, value in enumerate(self.start, start=1):
                f.write("S0 S%d 0 %e\n" % (index, sys.maxint))
                self.edges["S0 S%d" % index] = Edge(0, sys.maxint)

            for i in range(1, int(self.vhgcount) + 1):
                for index, value in enumerate(self.start, start=1):
                    f.write("S%d VHG%d %e %e\n" % (
                        index, i, self.sourcebw, self.vhgdelay))
                    self.edges["S%d VHG%d" % (index, i)] = Edge(self.sourcebw, self.vhgdelay)

                for index, value in enumerate(self.cdn, start=1):
                    f.write("VHG%d CDN%d %e %e\n" % (i, index, self.sourcebw * (1 - self.vcdnratio), self.cdndelay))
                    self.edges["VHG%d CDN%d" % (i, index)] = Edge(self.sourcebw * (1 - self.vcdnratio), self.cdndelay)

                for j in range(1, int(self.vcdncount) + 1):
                    f.write("VHG%d vCDN%d %e %e\n" % (i, j, self.sourcebw * self.vcdnratio, self.vcdndelay))
                    self.edges["VHG%d vCDN%d" % (i, j)] = Edge(self.sourcebw * self.vcdnratio, self.vcdndelay)

        with open("VHG.nodes.data", "w") as f:
            for i in range(1, int(self.vhgcount) + 1):
                f.write("VHG%d\n" % i)

        with open("VCDN.nodes.data", "w") as f:
            for i in range(1, int(self.vcdncount) + 1):
                f.write("vCDN%d\n" % i)

        with open("service.nodes.data", "w") as f:
            f.write("S0 0	\n")
            self.nodes["S0"] = Node(0)
            for index, value in enumerate(self.start, start=1):
                f.write("S%d 0	\n" % index)
                self.nodes["S%d" % index] = Node(0)

            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d 0\n" % index)
                self.nodes["CDN%d" % index] = Node(0)

            for j in range(1, int(self.vcdncount) + 1):
                f.write("vCDN%d	%e	\n" % (j, self.vcdncpu))
                self.nodes["vCDN%d" % j] = Node(self.vcdncpu)

            for i in range(1, int(self.vhgcount) + 1):
                f.write("VHG%d %e\n" % (i, float(self.vhgcpu)))
                self.nodes["VHG%d" % i] = Node(float(self.vhgcpu))

        with open("CDN.nodes.data", 'w') as f:
            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d\t%s\n" % (index, value))

        with open("starters.nodes.data", 'w') as f:
            for index, value in enumerate(self.start, start=1):
                f.write("S%d\t%s\n" % (index, value))

        with open("cdnmax.data", 'w') as f:
            f.write("%d" % self.max_cdn_to_use)
