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
        return cls(sla.bandwidth, 1, 1 * sla.delay / 4.0, 0.35, sla.delay * 100, 3 * sla.delay / 4.0, 10, 5, 1,
                   sla.start, sla.cdn)

    def __init__(self, sourcebw, vhgcount, vhgdelay, vcdnratio, cdndelay, vcdndelay, vcdncpu, vhgcpu, vcdncount, start,
                 cdn):
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

    def relax(self, relax_vhg=True, relax_vcdn=True):
        print "relaxation level\t%ld " % (self.vhgcount + self.vcdncount - 2)
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

            f.write("S LB %ld 0\n" % self.sourcebw)
            self.edges["S LB"] = Edge(self.sourcebw, 0)
            for i in range(1, int(self.vhgcount) + 1):
                f.write("LB VHG%d %lf %lf\n" % (i, self.sourcebw / self.vhgcount, self.vhgdelay))
                self.edges["LB VHG%d" % i] = Edge(self.sourcebw / self.vhgcount, self.vhgdelay)

                f.write("VHG%d CDN %lf %lf\n" % (
                    i, self.sourcebw / self.vhgcount * (1 - self.vcdnratio), self.cdndelay))
                # f.write("VHG%d CDN %lf %lf\n" % (                    i, 0, self.cdndelay))
                self.edges["VHG%d CDN" % i] = Edge(self.sourcebw / self.vhgcount * (1 - self.vcdnratio), self.cdndelay)
                # self.edges["VHG%d CDN" % i] = Edge(0, self.cdndelay)
                for j in range(1, int(self.vcdncount) + 1):
                    f.write("VHG%d vCDN%d %lf %lf\n" % (i, j,
                                                        self.sourcebw / (
                                                            self.vhgcount * self.vcdncount) * self.vcdnratio,
                                                        self.vcdndelay))
                    self.edges["VHG%d vCDN%d" % (i, j)] = Edge(self.sourcebw / (
                        self.vhgcount * self.vcdncount) * self.vcdnratio, self.vcdndelay)

        with open("service.nodes.data", "w") as f:
            f.write("S 0	\n")
            self.nodes["S"] = Node(0)
            f.write("LB 0	\n")
            self.nodes["LB"] = Node(0)
            f.write("CDN 0	\n")
            self.nodes["CDN"] = Node(0)
            for j in range(1, int(self.vcdncount) + 1):
                # f.write("vCDN%d	%lf	\n" % (j, self.vcdncpu / self.vcdncount))
                # self.nodes["vCDN%d" % j] = Node(self.vcdncpu / self.vcdncount)
                f.write("vCDN%d	%lf	\n" % (j, self.vcdncpu))
                self.nodes["vCDN%d" % j] = Node(self.vcdncpu)

            for i in range(1, int(self.vhgcount) + 1):
                f.write("VHG%d %lf\n" % (i, float(self.vhgcpu) / self.vhgcount))
                self.nodes["VHG%d" % i] = Node(float(self.vhgcpu) / self.vhgcount)

        with open("CDN.nodes.data", 'w') as f:
            f.write("%s \n" % self.cdn)

        with open("starters.nodes.data", 'w') as f:
            f.write("%s \n" % self.start)
