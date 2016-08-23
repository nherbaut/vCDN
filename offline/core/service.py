import logging
import os

from offline.core.combinatorial import clusterStart, get_vhg_cdn_mapping

OPTIM_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../optim')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


class Node:
    def __init__(self, cpu):
        self.cpu = cpu


class Edge:
    def __init__(self, bw):
        self.bw = bw


class ServiceSpec:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    @classmethod
    def fromFiles(cls):
        res = cls()
        with open(os.path.join(RESULTS_FOLDER, "service.edges.data"), 'r') as f:
            for data in f.read().split("\n"):
                if len(data) > 0:
                    data = data.replace("\t", " ").split(" ")
                    res.edges[data[0] + " " + data[1]] = Edge(float(data[2]))

        with open(os.path.join(RESULTS_FOLDER, "service.nodes.data"), 'r') as f:
            for data in f.read().split("\n"):
                if len(data) > 0:
                    data = data.replace("\t", " ").split(" ")

                    res.nodes[data[0]] = Node(float(data[1]))

        return res


class Service:
    @classmethod
    def cleanup(cls):

        for f in [os.path.join(RESULTS_FOLDER, "service.edges.data"),
                  os.path.join(RESULTS_FOLDER, "service.path.data"),
                  os.path.join(RESULTS_FOLDER, "service.path.delay.data"),
                  os.path.join(RESULTS_FOLDER, "service.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "CDN.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "starters.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "cdnmax.data"),
                  os.path.join(RESULTS_FOLDER, "VHG.nodes.data"),
                  os.path.join(RESULTS_FOLDER, "VCDN.nodes.data")]:
            if os.path.isfile(f):
                os.remove(f)

    @classmethod
    def fromSla(cls, sla):
        return cls(sla.bandwidth, 1, sla.delay, 0.35, 1, 5, 1,
                   sla.get_start_nodes(), sla.get_start_nodes(), sla.max_cdn_to_use, spvhg=False, id="default")

    def __init__(self, sourcebw, vhgcount, sla_delay, vcdnratio, vcdncpu, vhgcpu, vcdncount, start,
                 cdn, max_cdn_to_use, spvhg, id="default"):
        self.sourcebw = sourcebw
        self.vhgcount = vhgcount
        self.vcdnratio = vcdnratio
        self.sla_delay = sla_delay
        self.vcdncpu = vcdncpu
        self.vhgcpu = vhgcpu
        self.vcdncount = vcdncount
        self.start = start
        self.vhgcount = min(vhgcount, len(start))

        self.spec = ServiceSpec()
        self.cdn = cdn
        self.max_cdn_to_use = max_cdn_to_use
        self.service_id = 0
        self.vhg_hints = None
        self.spvhg = spvhg
        self.id = id

    def relax(self, relax_vhg=True, relax_vcdn=True):
        logging.debug("relax_vhg %s, relax_vcdn %s" % (relax_vhg, relax_vcdn))

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

    def write(self, append=False):
        '''
        write a service to the disk, as optimization parameters
        :return:  nothing
        '''
        if append:
            mode = "a"
        else:
            mode = "w"

        bw = {}
        self.spec.nodes = {}
        self.spec.edges = {}
        # VHG assignment
        if self.spvhg:
            source_vhg_assignment = clusterStart(self.start, self.vhgcount)

        if self.vhg_hints is not None:

            # match the vhg_hits with the service id
            tmp_int = self.vhg_hints
            self.vhg_hints = []
            for hint in tmp_int:
                h = hint.service_node_id.split("_")
                self.vhg_hints.append((hint.topo_node_id , h[0] + "_" + self.id))

            vhg_cdn_assignment = get_vhg_cdn_mapping(self.vhg_hints,
                                                     [(value.toponode_id, "CDN%d_%s" % (index, self.id)) for index, value in
                                                      enumerate(self.cdn, start=1)])
        else:
            vhg_cdn_assignment = None

        # write info on the edge
        with open(os.path.join(RESULTS_FOLDER, "service.edges.data"), mode) as f:
            for index, value in enumerate(self.start, start=1):
                e = Edge(0)
                self.spec.edges["S0_%s S%d_%s" % (self.id, index, self.id)] = e

            for index, value in enumerate(self.start, start=1):

                if self.spvhg:
                    assigned_vhg = source_vhg_assignment[value.toponode_id]
                else:
                    assigned_vhg = 1 + (index - 1) % self.vhgcount

                e = Edge(self.sourcebw / self.vhgcount)
                self.spec.edges["S%d_%s VHG%d_%s" % (index, self.id, assigned_vhg, self.id)] = e
                if "VHG%d" % assigned_vhg in bw:
                    bw["VHG%d_%s" % (assigned_vhg, self.id)] = bw["VHG%d_%s" % (
                        assigned_vhg, self.id)] + self.sourcebw / self.vhgcount
                else:
                    bw["VHG%d_%s" % (assigned_vhg, self.id)] = self.sourcebw / self.vhgcount

            for i in range(1, int(self.vhgcount) + 1):
                if len(self.cdn) > 0:
                    if vhg_cdn_assignment is None:
                        assigned_vhg = 1 + (i - 1) % len(self.cdn)
                    else:
                        assigned_vhg = int(vhg_cdn_assignment["VHG%d_%s" % (i, self.id)].split("CDN")[1].split("_")[0])
                    e = Edge(bw["VHG%d_%s" % (i, self.id)] * (1 - self.vcdnratio))
                    self.spec.edges["VHG%d_%s CDN%d_%s" % (i, self.id, assigned_vhg, self.id)] = e

            if self.vhgcount > 1:
                for i in range(1, int(self.vhgcount) + 1):
                    assigned_vcdn = 1 + (i - 1) % self.vcdncount
                    e = Edge(bw["VHG%d_%s" % (i, self.id)] * self.vcdnratio)
                    self.spec.edges["VHG%d_%s vCDN%d_%s" % (i, self.id, assigned_vcdn, self.id)] = e
            else:  # CAN increase vcdn up to len(start) is only relaxing vcdn
                for i in range(1, int(self.vhgcount) + 1):
                    for j in range(1, int(self.vcdncount) + 1):
                        e = Edge(bw["VHG%d_%s" % (i, self.id)] * self.vcdnratio / self.vcdncount)
                        self.spec.edges["VHG%d_%s vCDN%d_%s" % (i, self.id, j, self.id)] = e

            for key, value in self.spec.edges.items():
                f.write((key + " %e\n") % (value.bw))

        # compute info for delays
        service_path = []
        for index_src, src in enumerate(self.start, start=1):
            for index_vhg in range(1, int(self.vhgcount) + 1):
                for index_vcdn in range(1, int(self.vcdncount) + 1):
                    if "S%d_%s VHG%d_%s" % (index_src, self.id, index_vhg, self.id) in self.spec.edges.keys():
                        if "VHG%d_%s vCDN%d_%s" % (index_vhg, self.id, index_vcdn, self.id) in self.spec.edges.keys():
                            path_id = "S%d_%s_VHG%d_%s_vCDN%d_%s" % (
                                index_src, self.id, index_vhg, self.id, index_vcdn, self.id)
                            service_path.append(
                                (path_id, "S%d_%s" % (index_src, self.id), "VHG%d_%s" % (index_vhg, self.id)))
                            service_path.append(
                                (path_id, "VHG%d_%s" % (index_vhg, self.id), "vCDN%d_%s" % (index_vcdn, self.id)))

        # write path to associate e2e delay
        with open(os.path.join(RESULTS_FOLDER, "service.path.data"), mode) as f:
            for data in service_path:
                f.write("%s %s %s\n" % data)

        # write e2e delay constraint
        with open(os.path.join(RESULTS_FOLDER, "service.path.delay.data"), mode) as f:
            for x in set([i[0] for i in service_path]):
                f.write("%s %e\n" % (x, self.sla_delay))

        # write constraints on node capacity
        with open(os.path.join(RESULTS_FOLDER, "service.nodes.data"), mode) as f:
            f.write("S0_%s 0	\n" % self.id)
            self.spec.nodes["S0_%s" % self.id] = Node(0)
            for index, value in enumerate(self.start, start=1):
                f.write("S%d_%s 0	\n" % (index, self.id))
                self.spec.nodes["S%d_%s" % (index, self.id)] = Node(0)

            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d_%s 0\n" % (index, self.id))
                self.spec.nodes["CDN%d_%s" % (index, self.id)] = Node(0)

            if self.vhgcount > 1:
                for j in range(1, min(int(self.vcdncount) + 1, int(self.vhgcount) + 1)):
                    f.write("vCDN%d_%s	%e	\n" % (j, self.id, self.vcdncpu))
                    self.spec.nodes["vCDN%d_%s" % (j, self.id)] = Node(self.vcdncpu)
            else:  # can increase vcdn if vhg == 1
                for j in range(1, int(self.vcdncount) + 1):
                    f.write("vCDN%d_%s	%e	\n" % (j, self.id, self.vcdncpu))
                    self.spec.nodes["vCDN%d_%s" % (j, self.id)] = Node(self.vcdncpu)

            for i in range(1, int(self.vhgcount) + 1):
                f.write("VHG%d_%s %e\n" % (i, self.id, float(self.vhgcpu)))
                self.spec.nodes["VHG%d_%s" % (i, self.id)] = Node(float(self.vhgcpu))

        # write constraints on CDN placement
        with open(os.path.join(RESULTS_FOLDER, "CDN.nodes.data"), mode) as f:
            for index, value in enumerate(self.cdn, start=1):
                f.write("CDN%d_%s %s\n" % (index, self.id, value.toponode_id))


        # write constraints on starter placement
        with open(os.path.join(RESULTS_FOLDER, "starters.nodes.data"), mode) as f:
            for index, value in enumerate(self.start, start=1):
                f.write("S%d_%s %s\n" % (index, self.id, value.toponode_id))

        # write constraints on the maximum amont of cdn to use
        with open(os.path.join(RESULTS_FOLDER, "cdnmax.data"), 'w') as f:
            f.write("%d" % self.max_cdn_to_use)

        # write the names of the VHG Nodes (is it still used?)
        with open(os.path.join(RESULTS_FOLDER, "VHG.nodes.data"), mode) as f:
            for index in range(1, self.vhgcount + 1):
                f.write("VHG%d_%s\n" % (index, self.id))

        # write the names of the VCDN nodes (is it still used?)
        with open(os.path.join(RESULTS_FOLDER, "VCDN.nodes.data"), mode) as f:
            for index in range(1, self.vcdncount + 1):
                f.write("vCDN%d_%s\n" % (index, self.id))
