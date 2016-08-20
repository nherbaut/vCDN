#!/usr/bin/env python
#turn test.csv to proper time serie

from __future__ import print_function
import argparse
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.tsa as tsa
import pandas as pd
import datetime
from scipy.stats import norm
import numpy as np
from patsy import dmatrices

def generate(hours=None,input_path="../data/marseille.csv"):

    #read data
    df=pd.read_csv("test.csv",names=["time","values"])
    now=datetime.datetime.now()
    #shift observation according to time
    index=[]
    for key,value in enumerate(df["time"]):
      index.append(now+datetime.timedelta(days=value))
    #dump the ts
    ts=pd.Series(df["values"].values,index=index)
    ts.to_csv("test_orig.csv")
    ts.resample("1H").bfill().to_csv("test2.csv")
    ts.resample("6H").bfill().to_csv("test3.csv")
