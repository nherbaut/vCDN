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
        return cls(sla.bandwidth, 1, 2 * sla.delay / 4.0, 0.35, sla.delay * 100, 2 * sla.delay / 4.0, 10, 3, 1,
                   sla.start, sla.cdn,sla.max_cdn_to_use)

    def __init__(self, sourcebw, vhgcount, vhgdelay, vcdnratio, cdndelay, vcdndelay, vcdncpu, vhgcpu, vcdncount, start,
                 cdn,max_cdn_to_use):
        self.sourcebw = sourcebw

        self.vhgdelay = vhgdelay
        self.vhgcount = vhgcount
        self.vcdnratio = vcdnratio
        self.cdndelay = cdndelay
        self.vcdndelay = vcdndelay
        self.vcdncpu = vcdncpu
        self.vhgcpu = vhgcpu
        self.vcdncount = vcdncount
        self.start = start
        self.vhgcount = min(vhgcount,len(start))
        self.cdn = cdn
        self.nodes = {}
        self.edges = {}
        self.max_cdn_to_use=max_cdn_to_use

    def relax(self, relax_vhg=True, relax_vcdn=True):
        #print("relaxation level\t%e " % (self.vhgcount + self.vcdncount - 2))

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
        if(relax_vcdn and not relax_vhg):
            return self.vcdncount <= len(self.start)
        else: #CAN increase vcdn up to len(start) is only relaxing vcdn
            return (self.vcdncount <= self.vhgcount) and (self.vhgcount <=  len(self.start))

    def write(self):

        bw={}

        with open("service.edges.data", "w") as f:
            for index, value in enumerate(self.start, start=1):
                e=Edge(0, sys.maxint)
                self.edges["S0 S%d" % index] =e


            for index, value in enumerate(self.start, start=1):
                assigned_vhg=1+(index-1)%self.vhgcount

                e = Edge(self.sourcebw / self.vhgcount, self.vhgdelay)
                self.edges["S%d VHG%d" % (index, assigned_vhg)] = e
                if "VHG%d"%assigned_vhg in bw:
                    bw["VHG%d"%assigned_vhg]=bw["VHG%d"%assigned_vhg]+self.sourcebw / self.vhgcount
                else:
                    bw["VHG%d"%assigned_vhg]= self.sourcebw/ self.vhgcount

            for i in range(1, int(self.vhgcount) + 1):
                assigned_vhg=1+(i-1)%len(self.cdn)
                e = Edge(bw["VHG%d"%i] * (1 - self.vcdnratio)/len(self.cdn), self.cdndelay)
                self.edges["VHG%d CDN%d" % (i,assigned_vhg)] = e



            if self.vhgcount>1:
                for i in range(1, int(self.vhgcount) + 1):
                    assigned_vcdn=1+(i-1)%self.vcdncount
                    e = Edge(bw["VHG%d"%i] * self.vcdnratio, self.vcdndelay)
                    self.edges["VHG%d vCDN%d" % (i, assigned_vcdn)] = e
            else: #CAN increase vcdn up to len(start) is only relaxing vcdn
                for i in range(1, int(self.vhgcount) + 1):
                    for j in range(1, int(self.vcdncount) + 1):
                        e = Edge(bw["VHG%d"%i] * self.vcdnratio/self.vcdncount, self.vcdndelay)
                        self.edges["VHG%d vCDN%d" % (i, j)] = e

            for key,value in self.edges.items():
                f.write((key+" %e %e\n") % (value.bw, value.delay))


        with open("service.nodes.data", "w") as f:
            f.write("S0 0	\n")
            self.nodes["S0"] = Node(0)
            for index, value in enumerate(self.start, start=1):
                f.write("S%d 0	\n" % index)
                self.nodes["S%d" % index] = Node(0)


            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d 0\n" % index)
                self.nodes["CDN%d"%index] = Node(0)

            if self.vhgcount>1:
                for j in range(1, min( int(self.vcdncount) + 1, int(self.vhgcount) + 1)):
                    f.write("vCDN%d	%e	\n" % (j, self.vcdncpu))
                    self.nodes["vCDN%d" % j] = Node(self.vcdncpu)
            else: #can increase vcdn if vhg == 1
                for j in range(1, int(self.vcdncount) + 1):
                    f.write("vCDN%d	%e	\n" % (j, self.vcdncpu))
                    self.nodes["vCDN%d" % j] = Node(self.vcdncpu)

            for i in range(1, int(self.vhgcount) + 1):
                f.write("VHG%d %e\n" % (i, float(self.vhgcpu) ))
                self.nodes["VHG%d" % i] = Node(float(self.vhgcpu) )

        with open("CDN.nodes.data", 'w') as f:
            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d\t%s\n" % (index,value))

        with open("starters.nodes.data", 'w') as f:
            for index, value in enumerate(self.start, start=1):
                f.write("S%d\t%s\n" % (index, value))

        with open("cdnmax.data", 'w') as f:
            f.write("%d"%self.max_cdn_to_use)


        with open("VHG.nodes.data", 'w') as f:
            for index in range(1,self.vhgcount+1):
                f.write("VHG%d\n"%index)

        with open("VCDN.nodes.data", 'w') as f:
            for index in range(1,self.vcdncount+1):
                    f.write("vCDN%d\n"%index)