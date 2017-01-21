#!/usr/bin/env python

import argparse
import datetime
import logging
import os
import threading
import time
from collections import defaultdict
from scipy.stats import poisson, binom
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime as dt
from .dash import do_dash
import logging
import numpy as np


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
                 stalled=None,
                 threads=None):
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
        self.job=None
        self.threads=threads

    def run(self):
        self.threads[self.name]=True
        logging.debug("Starting " + self.name)
        do_dash(self.name, self.target_br, self.mini_buffer_seconds, self.maxi_buffer_seconds, self.movie_size,
                self.chunk_size,
                self.host, self.path, self.port, self.proxy_host, self.proxy_port, self.stalled)
        logging.debug("Exiting " + self.name)
        self.job.remove()
        del self.threads[self.name]


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
    threads={}



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
            if binom.rvs(10, 0.5) <= 3:  # pop
                postfix = "_hdpop"
            else:
                postfix = "_hd"

        else:  # sd
            target_br = args.target_br / 2.0
            movie_size = args.movie_size / 2.0
            postfix = "_sd"



        with open("dash_pool.log", "a+") as f:
            f.write("Thread-%000d will be %s and will start at %s\n"%(thread_no,postfix,next))

        thread_name="Thread-%000d-%s" % (thread_no, postfix)

        if args.proxy_host is None or args.proxy_port is None:


            thread1 = DashThread(thread_name, target_br,
                                 args.mini_buffer_seconds, args.maxi_buffer_seconds, movie_size, args.chunk_size,
                                 args.host, args.path + postfix, args.port, stalled=stalled,threads=threads)
        else:
            thread1 = DashThread(thread_name, target_br,
                                 args.mini_buffer_seconds, args.maxi_buffer_seconds, movie_size, args.chunk_size,
                                 args.host, args.path + postfix, args.port, args.proxy_host, args.proxy_port,
                                 stalled=stalled,threads=threads)
        job = scheduler.add_job(thread1.start, 'date', run_date=next)
        thread1.job=job


    scheduler.start()

    start = time.time()
    with open(stalled_file, "a+") as f:
        f.write("time,sum_stalled,count_stalled,count_users,stalled_hd,stalled_sd,active_session\n")


    sstalled_hd=pd.Series()
    sstalled_sd=pd.Series()
    users=pd.Series()

    now=dt.now()
    sstalled_hd[now]=0
    sstalled_sd[now]=0
    stalled_total_old=0
    stalled_hd_old=0


    while True:
        with open(stalled_file, "a") as f:
            now=dt.now()

            stalled_hd = sum([x[1] for x in [value for value in list(stalled.items()) if "hd" in value[0]]])
            stalled_total = sum(stalled.values())


            sstalled_hd[now]=stalled_hd-stalled_hd_old
            sstalled_sd[now]=(stalled_total - stalled_hd)-(stalled_total_old - stalled_hd_old)
            users[now]=args.user_count - len(scheduler.get_jobs())
            stalled_hd_old=stalled_hd
            stalled_total_old=stalled_total


            stalled_hd_rm=pd.rolling_mean(sstalled_hd.resample("1S",fill_method='bfill'),30)[-1]*60
            stalled_sd_rm=pd.rolling_mean(sstalled_sd.resample("1S",fill_method='bfill'),30)[-1]*60

            stalled_hd_value=stalled_hd_rm if not np.isnan(stalled_hd_rm) else 0
            stalled_sd_value=stalled_sd_rm if not np.isnan(stalled_sd_rm) else 0


            f.write("%lf,%d,%d,%d,%lf,%lf,%d\n" % (
                time.time() - start,
                sum(stalled.values()),
                len(stalled), args.user_count - len(scheduler.get_jobs()),
                stalled_hd_value,stalled_sd_value,len(threads)))
        time.sleep(1)

    scheduler.shutdown(wait=True)
