#!/usr/bin/env python
import argparse

import pandas as pd


def resample(file_in_path, file_out_path, rate="1H"):
    df = pd.read_csv(file_in_path, names=["time", "values"])
    ts = pd.Series(df["values"].values, index=pd.to_datetime(df["time"]))
    ts.resample(rate).mean().bfill().to_csv(file_out_path)


if "__main__" == __name__:
    parser = argparse.ArgumentParser(description='resample a file by the hour')
    parser.add_argument('--input', '-i', type=str)
    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('--rate', '-r', default="1H", type=str)

    args = parser.parse_args()

    resample(args.input, args.output, args.rate)
