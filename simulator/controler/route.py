# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import packet
from ryu.ofproto import ofproto_v1_3, os
# from ryu.ofproto import ofproto_v1_0, os
from ryu.topology.event import EventSwitchEnter

import numpy as np

import re

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../offline/results')

nodesSol = []
edgesSol = []
switch = {}
hosts = {}


def loadroutes(solutionsfile):
    with open(solutionsfile, "r") as sol:
        data = sol.read().split("\n")

        for line in data:
            matches = re.findall("^x\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                nodesSol.append(matches[0])
                continue
            matches = re.findall("^y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                edgesSol.append(matches[0])
                continue
    for edge in edgesSol:
        if not int(edge[0], 16) in switch:
            switch[int(edge[0], 16)] = []
        switch[int(edge[0], 16)].append(edge)
    # permute colon 0 with 1 and 2 with 3
    edge2 = np.array(edgesSol)
    edgep = np.array(edgesSol)
    edgep[:, 1] = edge2[:, 0]
    edgep[:, 0] = edge2[:, 1]
    edgep[:, 2] = edge2[:, 3]
    edgep[:, 3] = edge2[:, 2]

    for edge in edgep.tolist():
        if not int(edge[0], 16) in switch:
            switch[int(edge[0], 16)] = []
        switch[int(edge[0], 16)].append(edge)
    i = 0
    for node in nodesSol:
        if node[1] != "S0":
            i += 1;
            name = node[1]
            ip = '10.0.0.%i' % i
            if "VHG" in node[1]:
                hosts[node[1]] = ip
            elif "vCDN" in node[1]:
                hosts[node[1]] = ip
            elif "S" in node[1]:
                hosts[node[1]] = ip
            elif "CDN" in node[1]:
                hosts[node[1]] = ip
            else:
                print 'error'
    pass


class MWCController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    # OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def is_slow(self, eth_src):
        return int(eth_src.replace(':', ''), 16) % 2 == 0

    def __init__(self, *args, **kwargs):
        super(MWCController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.switches = {}
        solutionsFile = os.path.join(RESULTS_FOLDER, "solutions.data")
        loadroutes(solutionsFile)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        self.logger.debug("%s", str(mod))
        datapath.send_msg(mod)

    @set_ev_cls(EventSwitchEnter, MAIN_DISPATCHER)
    def _welcome(self, ev):
        dpid = ev.switch.dp.id
        # print(int(ev.switch.dp.id,16))
        self.switches[dpid] = ev.switch.dp
        parser = ev.switch.dp.ofproto_parser
        if dpid in switch:
            for flow in switch[dpid]:
                if ((flow[2] != 'S0') and (flow[3] != 'S0')):

                    self.add_flow(ev.switch.dp,
                                  1,
                                  match=parser.OFPMatch(ipv4_src=self._ipv4_text_to_int(hosts[flow[2]]),
                                                        ipv4_dst=self._ipv4_text_to_int(hosts[flow[3]])),
                                  actions=[parser.OFPActionOutput(int(flow[1]))])


                    # if (dpid)
                    # if dpid == 0x3001 or dpid == 0x3002:  # slow or fast switch
                    #     self.add_flow(ev.switch.dp, 1, match=parser.OFPMatch(in_port=1), actions=[parser.OFPActionOutput(2)])
                    #     self.add_flow(ev.switch.dp, 1, match=parser.OFPMatch(in_port=2), actions=[parser.OFPActionOutput(1)])
                    # if dpid == 0x3003:  # access upstream
                    #     self.add_flow(ev.switch.dp, 1, match=parser.OFPMatch(in_port=1), actions=[parser.OFPActionOutput(3)])
                    #     self.add_flow(ev.switch.dp, 1, match=parser.OFPMatch(in_port=2), actions=[parser.OFPActionOutput(3)])

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch

        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        out = None
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        if eth.ethertype not in [0x86DD, 0x88CC]:
            self.logger.info("packet in %d @ %ld " % (eth.ethertype, time.time()))

        self.mac_to_port[eth.src] = in_port

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        arps = pkt.get_protocols(arp.arp)
        ipv4s = pkt.get_protocols(ipv4.ipv4)

        if (len(ipv4s) > 0):  # ipv4
            self.logger.info("[%lf] ipv4 from %s to %s on %d" % (time.time(), ipv4s[0].src, ipv4s[0].dst, datapath.id))

        if datapath.id in switch:
            for flow in switch[datapath.id]:
                if ((flow[2] != 'S0') and (flow[3] != 'S0')):

                    self.add_flow(datapath,
                                  1,
                                  match=parser.OFPMatch(ipv4_src=hosts[flow[2]],
                                                        ipv4_dst=hosts[flow[3]]),
                                  actions=[parser.OFPActionOutput(int(flow[1]))])


        # if datapath.id == 0x3000:  # core
        #
        #     core_next_port = None
        #     slow = self.is_slow(eth.src)
        #     if slow:
        #         core_next_port = 1
        #
        #     else:
        #         core_next_port = 2
        #
        #     if len(arps) > 0:  # installing downstream flow
        #         arp_message = arps[0]
        #
        #         self.add_flow(self.switches[0x3000], 1, match=parser.OFPMatch(eth_dst=arp_message.src_mac),
        #                       actions=[parser.OFPActionOutput(in_port)])
        #         self.add_flow(self.switches[0x3000], 1, match=parser.OFPMatch(eth_src=arp_message.src_mac),
        #                       actions=[parser.OFPActionOutput(core_next_port)])
        #
        #         self.add_flow(self.switches[0x3003], 1,
        #                       match=parser.OFPMatch(in_port=3, eth_dst=arp_message.src_mac),
        #                       actions=[parser.OFPActionOutput(core_next_port)])
        #
        #     if len(ipv4s) > 0:  # installing downstream flow
        #         ip_message = ipv4s[0]
        #         if ip_message.dst != "255.255.255.255":
        #             self.add_flow(self.switches[0x3000], 1, match=parser.OFPMatch(ipv4_dst=ip_message.src),
        #                           actions=[parser.OFPActionOutput(in_port)])
        #             self.add_flow(self.switches[0x3000], 1, match=parser.OFPMatch(ipv4_src=ip_message.src),
        #                           actions=[parser.OFPActionOutput(core_next_port)])
        #             self.add_flow(self.switches[0x3001], 1, match=parser.OFPMatch(in_port=3, ipv4_dst=ip_message.src, ),
        #                           actions=[parser.OFPActionOutput(in_port)])
        #
        #     if in_port > 100 and core_next_port:  # upstream packet_out
        #         out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
        #                                   in_port=in_port, actions=[parser.OFPActionOutput(core_next_port)], data=data)
        #
        #     else:  # downstearm
        #         self.logger.debug("discarding downstream packet_in")

        if out:
            datapath.send_msg(out)

    def _ipv4_text_to_int(self, ip_text):
        """convert ip v4 string to integer."""
        import struct
        from ryu.lib import addrconv
        if ip_text is None:
            return None
        assert isinstance(ip_text, str)
        return struct.unpack('!I', addrconv.ipv4.text_to_bin(ip_text))[0]
