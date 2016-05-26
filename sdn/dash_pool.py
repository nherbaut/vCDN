#!/usr/bin/env python

import argparse
import datetime
import logging
import os
import threading
import time
from collections import defaultdict
from scipy.stats import poisson, binom

from apscheduler.schedulers.background import BackgroundScheduler

from dash import do_dash
import logging



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
                 proxy_port=None,
                 stalled=None):
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
        self.stalled = stalled

    def run(self):
        logging.debug("Starting " + self.name)
        do_dash(self.name, self.target_br, self.mini_buffer_seconds, self.maxi_buffer_seconds, self.movie_size,
                self.chunk_size,
                self.host, self.path, self.port, self.proxy_host, self.proxy_port, self.stalled)
        logging.debug("Exiting " + self.name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='1 iteration for solver')

    parser.add_argument('--name', default="anonymous")
    parser.add_argument('--arrival_time', default=3.0, type=float)
    parser.add_argument('--user_count', default=10, type=int)

    parser.add_argument('--target_br', help="target bitrate", default=5 * 1000 * 1000, type=int)
    parser.add_argument('--mini_buffer_seconds', default=10, type=int)
    parser.add_argument('--maxi_buffer_seconds', default=30, type=int)
    parser.add_argument('--movie_size', default=1000 * 1000 * 1000, type=int)
    parser.add_argument('--chunk_size', default=2 * 1000 * 1000, type=int)
    parser.add_argument('--host', default="mirlitone.com")
    parser.add_argument('--path', default="big_buck_bunny.mp4")
    parser.add_argument('--port', default="80")
    parser.add_argument('--proxy_host')
    parser.add_argument('--proxy_port')

    args = parser.parse_args()



    scheduler = BackgroundScheduler()

    arrival_time = poisson.rvs(args.arrival_time, size=args.user_count).tolist()
    stalled = defaultdict(int)
    stalled_file = "stalled-%s.log" % args.name
    if os.path.isfile(stalled_file):
        os.remove(stalled_file)

    next = datetime.datetime.now()
    while len(arrival_time) > 0:
        thread_no=(args.user_count - len(arrival_time))
        next += datetime.timedelta(0, arrival_time.pop())

        if binom.rvs(1, 0.5) == 1:  # hd

            target_br = args.target_br
            movie_size = args.movie_size
            if binom.rvs(5, 0.5) == 1:  # pop
                postfix = "_hdpop"
            else:
                postfix = "_hd"

        else:  # sd
            target_br = args.target_br / 2.0
            movie_size = args.movie_size / 2.0
            postfix = "_sd"



        with open("dash_pool.log", "a+") as f:
            f.write("Thread-%000d will be %s and will start at %s\n"%(thread_no,postfix,next))


        if args.proxy_host is None or args.proxy_port is None:

            thread1 = DashThread("Thread-%000d-%s" % (thread_no, postfix), target_br,
                                 args.mini_buffer_seconds, args.maxi_buffer_seconds, movie_size, args.chunk_size,
                                 args.host, args.path + postfix, args.port, stalled=stalled)
        else:
            thread1 = DashThread("Thread-%000d-%s" % (thread_no, postfix), target_br,
                                 args.mini_buffer_seconds, args.maxi_buffer_seconds, movie_size, args.chunk_size,
                                 args.host, args.path + postfix, args.port, args.proxy_host, args.proxy_port,
                                 stalled=stalled)
        job = scheduler.add_job(thread1.start, 'date', run_date=next)

    scheduler.start()

    start = time.time()
    with open(stalled_file, "a+") as f:
        f.write("time,sum_stalled,count_stalled,count_users,stalled_hd,stalled_sd\n")

    while True:
        with open(stalled_file, "a") as f:
            stalled_hd = sum([x[1] for x in filter(lambda value: "hd" in value[0], stalled.items())])
            stalled_total = sum(stalled.values())
            f.write("%lf,%d,%d,%d,%d,%d\n" % (
                time.time() - start,
                sum(stalled.values()),
                len(stalled), args.user_count - len(scheduler.get_jobs()),
                    stalled_hd, stalled_total - stalled_hd))
        time.sleep(1)

    scheduler.shutdown(wait=True)
