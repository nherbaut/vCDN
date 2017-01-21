import json
import os
import threading
import time
from xmlrpc.server import SimpleXMLRPCServer,SimpleXMLRPCRequestHandler
from operator import attrgetter

from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

from . import route
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../offline/results')

JSON_MAX = 300

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/', '/RPC2',)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    # Add these headers to all responses
    def end_headers(self):
        self.send_header("Access-Control-Allow-Headers",
                         "Origin, X-Requested-With, Content-Type, Accept")
        self.send_header("Access-Control-Allow-Origin", "*")
        SimpleXMLRPCRequestHandler.end_headers(self)

class SimpleMonitor(route.MWCController):
    def __init__(self, *args, **kwargs):
        super(SimpleMonitor, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.totals = {}
        self.slices = {}
        # self.bwstats = BandwidthStats(self.topo)
        self.monitor_thread = hub.spawn(self._monitor)

        self.rpcStart()
        self.logStart()

    def rpcStart(self):
        self.server = SimpleXMLRPCServer(("0.0.0.0", 8000),requestHandler=RequestHandler, logRequests=False)
        self.server.register_instance(self)
        self.server.register_function(self.rpcLoadPolicy, "load")
        # self.server.register_function(self.rpcLoadPolicy, "load")
        # self.server.register_function(self.rpcCurrentPolicy, "current")
        thread = threading.Thread(target=self.server.serve_forever)
        thread.start()
        self.logger.info("starting rpc server")



    def logStart(self):
        import http.server
        import socketserver

        PORT = 9998

        Handler = http.server.SimpleHTTPRequestHandler

        httpd = socketserver.TCPServer(("", PORT), Handler)

        print(("serving at port", PORT))

        thread = threading.Thread(target= httpd.serve_forever)
        thread.start()

        pass

    def rpcLoadPolicy(self, nbHost, nbSlow):
        str = "rpc request load {0} host with  {1} slow (befort {2} host with  {3} slow ))".format(nbHost, nbSlow,
                                                                                                   route.nbHost,
                                                                                                   route.nbSlow)
        self.logger.info(str)
        route.nbHost = nbHost
        route.nbSlow = nbSlow
        return (True, str)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in list(self.datapaths.values()):
                self._request_stats(dp)
            hub.sleep(1)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    def addHostBwStat(self, serverName, rxbytes, txbytes):
        host_rx = txbytes
        host_tx = rxbytes

        if serverName not in self.totals:
            self.totals[serverName] = []
            self.totals[serverName].append({'in': 0,
                                            'out': 0
                                            })
            self.slices[serverName] = []

        last = self.totals[serverName][-1]
        rxslice = rxbytes - last['in']
        txslice = txbytes - last['out']

        self.slices[serverName].append({'in': rxslice, 'out': txslice, 'time': time.time()})
        self.totals[serverName].append({'in': rxbytes, 'out': txbytes, 'time': time.time()})

        if len(self.totals[serverName]) > JSON_MAX:
            start = len(self.totals[serverName]) - JSON_MAX
            self.totals[serverName] = self.totals[serverName][start:]
            self.slices[serverName] = self.slices[serverName][start:]



    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        # self.logger.info('datapath         port     '
        #                  'rx-pkts  rx-bytes rx-error '
        #                  'tx-pkts  tx-bytes tx-error')
        # self.logger.info('---------------- -------- '
        #                  '-------- -------- -------- '
        #                  '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):

            # self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
            #                  ev.msg.datapath.id, stat.port_no,
            #                  stat.rx_packets, stat.rx_bytes, stat.rx_errors,
            #                  stat.tx_packets, stat.tx_bytes, stat.tx_errors)

            # if (ev.msg.datapath.id == route.):
            #     # self.logger.info("equal 1000 (slow)")
            #     if (stat.port_no == 1):
                    # self.logger.info("equal 1")
            self.addHostBwStat("%s.%s"%(ev.msg.datapath.id, stat.port_no), stat.rx_bytes, stat.tx_bytes)
            b = json.dumps(self.slices["%s.%s"%(ev.msg.datapath.id, stat.port_no)])
            self.toJsonFile(b, "./%s.%s.json"%(ev.msg.datapath.id, stat.port_no))


    def toJsonFile(self, b, nameFile):
        # print b
        with open(os.path.join(RESULTS_FOLDER,nameFile), "w") as text_file:
            text_file.write(str(b))

