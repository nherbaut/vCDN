#!/usr/bin/env python

import argparse
import datetime as dt

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(
    description='tell which phase should be used according to link 31 bw, 0 = no change, 1 = change to 1, 2 = change to 2')
parser.add_argument('--file_path', default="../controller/31.txt")
parser.add_argument('--column_id', default=13, type=int)
parser.add_argument('--index_id', default=0, type=int)
parser.add_argument('--max_threshold', default=12000000.0, type=float)
parser.add_argument('--min_threshold', default=3000000.0, type=float)
parser.add_argument('--phase_data_file', default="phase.data")

args = parser.parse_args()

with open(args.phase_data_file, "r") as f:
    phase = int(f.read())

now = dt.datetime.now()
rolling_win = 25

with open(args.file_path) as f:
    d = f.read().split("\n")
    d = d[1:-1]

if len(d) <= 30:
    if phase == 1:
        res = 0
    else:
        res = 1
else:

    d = [[float(y) for y in x.split(",")] for x in d]

    s = pd.Series()
    for value in d:
        s[now + dt.timedelta(seconds=value[args.index_id])] = value[args.column_id]

    average = pd.rolling_mean(s.resample("1S", fill_method='bfill'), rolling_win )[-1]
    average = average if not np.isnan(average) else 0


    if average > args.max_threshold:
        if phase==1:
            res=2
        else:
            res=0
    elif average >= args.min_threshold:
            res=0
    else:
        if phase==1:
            res=0
        else:
            res=1


print(res)
