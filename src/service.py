import sys
from combinatorial import clusterStart, get_vhg_cdn_mapping
import logging
class Node:
    def __init__(self, cpu):
        self.cpu = cpu


class Edge:
    def __init__(self, bw):
        self.bw = bw



class Service:

    @classmethod
    def fromSla(cls, sla):
        return cls(sla.bandwidth, 1, sla.delay, 0.35, 10, 3, 1,
                   sla.start, sla.cdn, sla.max_cdn_to_use,spvhg=False)

    def __init__(self, sourcebw, vhgcount, sla_delay, vcdnratio, vcdncpu, vhgcpu, vcdncount, start,
                 cdn, max_cdn_to_use,spvhg):
        self.sourcebw = sourcebw


        self.vhgcount = vhgcount
        self.vcdnratio = vcdnratio
        self.sla_delay = sla_delay
        self.vcdncpu = vcdncpu
        self.vhgcpu = vhgcpu
        self.vcdncount = vcdncount
        self.start = start
        self.vhgcount = min(vhgcount, len(start))

        self.nodes = {}
        self.edges = {}
        self.cdn = cdn
        self.max_cdn_to_use = max_cdn_to_use
        self.service_id = 0
        self.vhg_hints=None
        self.spvhg=spvhg



    def relax(self, relax_vhg=True, relax_vcdn=True):
        logging.debug("relax_vhg %s, relax_vcdn %s" % (relax_vhg,relax_vcdn))


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
        if (relax_vcdn and not relax_vhg):
            return self.vcdncount <= len(self.start)
        else:  # CAN increase vcdn up to len(start) is only relaxing vcdn
            return (self.vcdncount <= self.vhgcount) and (self.vhgcount <= len(self.start))

    def write(self):
        '''
        write a service to the disk, as optimization parameters
        :return:  nothing
        '''

        bw = {}
        self.nodes = {}
        self.edges = {}
        #VHG assignment
        if self.spvhg:
            source_vhg_assignment= clusterStart(self.start,self.vhgcount)

        if  self.vhg_hints is not None:
            vhg_cdn_assignment=get_vhg_cdn_mapping(self.vhg_hints,[(value,"CDN%d"%index) for index,value in enumerate(self.cdn,start=1)])
        else:
            vhg_cdn_assignment=None


        #write info on the edge
        with open("service.edges.data", "w") as f:
            for index, value in enumerate(self.start, start=1):
                e = Edge(0)
                self.edges["S0 S%d" % index] = e

            for index, value in enumerate(self.start, start=1):



                if self.spvhg:
                    assigned_vhg = source_vhg_assignment[value]
                else:
                    assigned_vhg = 1 + (index - 1) % self.vhgcount

                e = Edge(self.sourcebw / self.vhgcount)
                self.edges["S%d VHG%d" % (index, assigned_vhg)] = e
                if "VHG%d" % assigned_vhg in bw:
                    bw["VHG%d" % assigned_vhg] = bw["VHG%d" % assigned_vhg] + self.sourcebw / self.vhgcount
                else:
                    bw["VHG%d" % assigned_vhg] = self.sourcebw / self.vhgcount

            for i in range(1, int(self.vhgcount) + 1):
                if len(self.cdn)>0:
                    if vhg_cdn_assignment is None:
                        assigned_vhg = 1 + (i - 1) % len(self.cdn)
                    else:
                        assigned_vhg = int(vhg_cdn_assignment["VHG%d" % i].split("CDN")[1])
                    e = Edge(bw["VHG%d" % i] * (1 - self.vcdnratio))
                    self.edges["VHG%d CDN%d" % (i, assigned_vhg)] = e

            if self.vhgcount > 1:
                for i in range(1, int(self.vhgcount) + 1):
                    assigned_vcdn = 1 + (i - 1) % self.vcdncount
                    e = Edge(bw["VHG%d" % i] * self.vcdnratio)
                    self.edges["VHG%d vCDN%d" % (i, assigned_vcdn)] = e
            else:  # CAN increase vcdn up to len(start) is only relaxing vcdn
                for i in range(1, int(self.vhgcount) + 1):
                    for j in range(1, int(self.vcdncount) + 1):
                        e = Edge(bw["VHG%d" % i] * self.vcdnratio / self.vcdncount)
                        self.edges["VHG%d vCDN%d" % (i, j)] = e



            for key, value in self.edges.items():
                f.write((key + " %e\n") % (value.bw))


        #compute info for delays
        service_path = []
        for index_src, src in enumerate(self.start, start=1):
            for index_vhg in range(1, int(self.vhgcount) + 1):
                for index_vcdn in range(1, int(self.vcdncount) + 1):
                    if "S%d VHG%d" % (index_src, index_vhg) in self.edges.keys():
                        if "VHG%d vCDN%d" % (index_vhg, index_vcdn) in self.edges.keys():
                            path_id="S%d_VHG%d_vCDN%d" % (index_src, index_vhg, index_vcdn)
                            service_path.append((path_id, "S%d" % index_src, "VHG%d" % index_vhg))
                            service_path.append((path_id, "VHG%d" % index_vhg, "vCDN%d" % index_vcdn))


        #write path to associate e2e delay
        with open("service.path.data", "w") as f:
                for data in service_path:
                    f.write("%s %s %s\n"%data)

        #write e2e delay constraint
        with open("service.path.delay.data","w") as f:
                for x in set([i[0] for i in service_path]):
                    f.write("%s %e\n"%(x,self.sla_delay))

        #write constraints on node capacity
        with open("service.nodes.data", "w") as f:
            f.write("S0 0	\n")
            self.nodes["S0"] = Node(0)
            for index, value in enumerate(self.start, start=1):
                f.write("S%d 0	\n" % index)
                self.nodes["S%d" % index] = Node(0)

            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d 0\n" % index)
                self.nodes["CDN%d" % index] = Node(0)

            if self.vhgcount > 1:
                for j in range(1, min(int(self.vcdncount) + 1, int(self.vhgcount) + 1)):
                    f.write("vCDN%d	%e	\n" % (j, self.vcdncpu))
                    self.nodes["vCDN%d" % j] = Node(self.vcdncpu)
            else:  # can increase vcdn if vhg == 1
                for j in range(1, int(self.vcdncount) + 1):
                    f.write("vCDN%d	%e	\n" % (j, self.vcdncpu))
                    self.nodes["vCDN%d" % j] = Node(self.vcdncpu)

            for i in range(1, int(self.vhgcount) + 1):
                f.write("VHG%d %e\n" % (i, float(self.vhgcpu)))
                self.nodes["VHG%d" % i] = Node(float(self.vhgcpu))

        #write constraints on CDN placement
        with open("CDN.nodes.data", 'w') as f:
            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d\t%s\n" % (index, value))

        #write constraints on starter placement
        with open("starters.nodes.data", 'w') as f:
            for index, value in enumerate(self.start, start=1):
                f.write("S%d\t%s\n" % (index, value))

        #write constraints on the maximum amont of cdn to use
        with open("cdnmax.data", 'w') as f:
            f.write("%d" % self.max_cdn_to_use)

        #write the names of the VHG Nodes (is it still used?)
        with open("VHG.nodes.data", 'w') as f:
            for index in range(1, self.vhgcount + 1):
                f.write("VHG%d\n" % index)

        #write the names of the VCDN nodes (is it still used?)
        with open("VCDN.nodes.data", 'w') as f:
            for index in range(1, self.vcdncount + 1):
                f.write("vCDN%d\n" % index)
