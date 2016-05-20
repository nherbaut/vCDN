#!/usr/bin/env python
import httplib
import time
import argparse

parser = argparse.ArgumentParser(description='1 iteration for solver')

parser.add_argument('--target_br', help="target bitrate", default=5 * 1000 * 1000,type=int)
parser.add_argument('--mini_buffer_seconds',  default=10,type=int)
parser.add_argument('--maxi_buffer_seconds',  default=30,type=int)
parser.add_argument('--movie_size',  default=1000 * 1000 * 1000,type=int)
parser.add_argument('--chunk_size',  default=2 * 1000 * 1000,type=int)
parser.add_argument('--host',  default="mirlitone.com")
parser.add_argument('--path',  default="big_buck_bunny.mp4")

args = parser.parse_args()



TARGET_BITRATE = args.target_br
m = args.mini_buffer_seconds
M = args.maxi_buffer_seconds



CHUNK_SIZE = args.chunk_size
MOVIE_SIZE = args.movie_size

HOST=args.host
PATH=args.path

def download_bytes(bytes_count=100):
    conn = httplib.HTTPConnection(HOST)
    conn.request("GET", '/'+PATH, headers={'Range': 'bytes=0-%d' % bytes_count})
    resp = conn.getresponse()
    return int(resp.getheader("content-length"))


buffering = True
buffer = 0
total_bytes_left = MOVIE_SIZE
tic = time.time()
while total_bytes_left > 0:
    time_spent=time.time() - tic
    tic = time.time()
    print "buffering: %s\ttotal_bytes_left: %d\t buffer left %d \t consumed %d bytes in %lf seconds" % (buffering,total_bytes_left,buffer,time_spent* TARGET_BITRATE,time_spent)
    data_consumed = min(buffer, time_spent * TARGET_BITRATE)
    total_bytes_left -= data_consumed
    buffer -= data_consumed

    if buffer <= m * TARGET_BITRATE:
        buffer += download_bytes(CHUNK_SIZE)
        buffering = True
    elif buffer <= M * TARGET_BITRATE and buffering:
        buffer += download_bytes(CHUNK_SIZE)
        if buffer > M * TARGET_BITRATE:
            buffering = False
    else:
        time.sleep(1)
