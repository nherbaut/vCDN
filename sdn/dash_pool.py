#!/usr/bin/env python

import argparse
import datetime
import logging
import threading
import time
from scipy.stats import poisson

from apscheduler.schedulers.background import BackgroundScheduler

from dash import do_dash

logging.basicConfig(filename='dash_pool.log', level=logging.DEBUG)


class DashThread(threading.Thread):
    def __init__(self,
                 name,
                 target_br,
                 mini_buffer_seconds,
                 maxi_buffer_seconds,
                 movie_size,
                 chunk_size,
                 host,
                 path,
                 port,
                 proxy_host=None,
                 proxy_port=None):
        threading.Thread.__init__(self)
        self.name = name
        self.target_br = target_br
        self.mini_buffer_seconds = mini_buffer_seconds
        self.maxi_buffer_seconds = maxi_buffer_seconds
        self.movie_size = movie_size
        self.chunk_size = chunk_size

        self.host = host
        self.path = path
        self.port = port
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def run(self):
        logging.debug("Starting " + self.name)
        do_dash(self.name,self.target_br, self.mini_buffer_seconds, self.maxi_buffer_seconds, self.movie_size, self.chunk_size,
                self.host, self.path, self.port,self.proxy_host ,self.proxy_port )
        logging.debug("Exiting " + self.name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='1 iteration for solver')

    parser.add_argument('--arrival_time', default=3.0, type=float)
    parser.add_argument('--user_count', default=100, type=int)

    parser.add_argument('--target_br', help="target bitrate", default=5 * 1000 * 1000, type=int)
    parser.add_argument('--mini_buffer_seconds', default=10, type=int)
    parser.add_argument('--maxi_buffer_seconds', default=30, type=int)
    parser.add_argument('--movie_size', default=1000 * 1000 * 1000, type=int)
    parser.add_argument('--chunk_size', default=2 * 1000 * 1000, type=int)
    parser.add_argument('--host', default="mirlitone.com")
    parser.add_argument('--path', default="big_buck_bunny.mp4")
    parser.add_argument('--port', default="80")
    parser.add_argument('--proxy_host' )
    parser.add_argument('--proxy_port' )

    args = parser.parse_args()

    scheduler = BackgroundScheduler()

    arrival_time = poisson.rvs(args.arrival_time, size=args.user_count).tolist()

    next = datetime.datetime.now()
    while len(arrival_time) > 0:
        next += datetime.timedelta(0, arrival_time.pop())
        if args.proxy_host is None or args.proxy_port is None:
            thread1 = DashThread("Thread-%000d" % (args.user_count - len(arrival_time)), args.target_br,
                                 args.mini_buffer_seconds, args.maxi_buffer_seconds, args.movie_size, args.chunk_size,
                                 args.host, args.path, args.port)
        else:
            thread1 = DashThread("Thread-%000d" % (args.user_count - len(arrival_time)), args.target_br,
                             args.mini_buffer_seconds, args.maxi_buffer_seconds, args.movie_size, args.chunk_size,
                             args.host, args.path, args.port, args.proxy_host, args.proxy_port)
        job = scheduler.add_job(thread1.start, 'date', run_date=next)

    scheduler.start()

    while len(scheduler.get_jobs()) > 0:
        time.sleep(1)

    scheduler.shutdown(wait=True)
