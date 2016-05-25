#!/usr/bin/env python
import argparse
import httplib
import logging
import time

logging.basicConfig(filename='dash.log', level=logging.DEBUG)


def download_bytes(host, path, port, bytes_count, proxy_host, proxy_port):

    try:
        if proxy_host is not None and proxy_port is not None:
            conn = httplib.HTTPConnection(proxy_host, proxy_port)
            conn.request(method="GET", url='http://%s:%s/%s' % (host, port, path),
                         headers={'Range': 'bytes=0-%d' % bytes_count})

        else:
            conn = httplib.HTTPConnection('%s:%s' % (host, port))
            conn.request("GET", '/%s' % (path), headers={'Range': 'bytes=0-%d' % bytes_count})

        resp = conn.getresponse()
        if resp.getheader("content-length") is not None:
            return int(resp.getheader("content-length"))
        else:
            return 0
    except:
        print "failed to download"
        return 0


def do_dash(name, target_br, mini_buffer_seconds, maxi_buffer_seconds, movie_size, chunk_size, host, path, port,
            proxy_host,
            proxy_port):
    TARGET_BITRATE = target_br
    m = mini_buffer_seconds
    M = maxi_buffer_seconds

    CHUNK_SIZE = chunk_size
    MOVIE_SIZE = movie_size

    HOST = host
    PATH = path
    PORT = port

    buffering = True
    buffer = 0
    total_bytes_left = MOVIE_SIZE
    tic = time.time()
    while total_bytes_left > 0:
        time_spent = time.time() - tic
        tic = time.time()
        logging.debug("buffering: %s\ttotal_bytes_left: %d\t buffer left %d \t consumed %d bytes in %lf seconds" % (
            buffering, total_bytes_left, buffer, time_spent * TARGET_BITRATE, time_spent))
        data_consumed = min(buffer, time_spent * TARGET_BITRATE)
        total_bytes_left -= data_consumed
        buffer -= data_consumed
        if buffer == 0 and time_spent >= 10:
            print "%d\t%s\tstalled!" % (time.time(), name)

        if buffer <= m * TARGET_BITRATE:
            buffer += download_bytes(host, path, port, CHUNK_SIZE, proxy_host, proxy_port)
            # logging.debug("switched on buffering")
            buffering = True
        elif buffer <= M * TARGET_BITRATE and buffering:
            buffer += download_bytes(HOST, PATH, PORT, CHUNK_SIZE, proxy_host, proxy_port)
            if buffer > M * TARGET_BITRATE:
                # logging.debug("switched off buffering")
                buffering = False
        else:
            time.sleep(float(buffer - m * TARGET_BITRATE) / TARGET_BITRATE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='1 iteration for solver')

    parser.add_argument('--target_br', help="target bitrate", default=5 * 1000 * 1000, type=int)
    parser.add_argument('--mini_buffer_seconds', default=10, type=int)
    parser.add_argument('--maxi_buffer_seconds', default=30, type=int)
    parser.add_argument('--movie_size', default=1000 * 1000 * 1000, type=int)
    parser.add_argument('--chunk_size', default=1000 * 1000, type=int)
    parser.add_argument('--host', default="mirlitone.com")
    parser.add_argument('--path', default="big_buck_bunny.mp4")
    parser.add_argument('--port', default="8080")
    parser.add_argument('--proxy_host', default=None)
    parser.add_argument('--proxy_port', default=None)

    args = parser.parse_args()

    do_dash("only_child", args.target_br, args.mini_buffer_seconds, args.maxi_buffer_seconds, args.movie_size,
            args.chunk_size,
            args.host, args.path, args.port, args.proxy_host, args.proxy_port)
