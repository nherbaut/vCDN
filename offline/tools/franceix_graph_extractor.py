#!/usr/bin/env python
import argparse
from datetime import datetime
import re
import PIL
import PIL.ImageFilter
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
from pylab import *


def extract_data_from_graph(file_path):
    win = 5
    im = Image.open(file_path).convert("RGB")
    im = im.crop((67, 45, 964, 297))
    im = im.filter(PIL.ImageFilter.CONTOUR)
    data = np.array(im)
    red, green, blue = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    mask = (red < 150) | (green > 50) | (blue > 50)
    x = []
    y = []
    for i in np.arange(0, len(mask.T), win):
        # print ((i+win/2.0)/len(mask.T))
        # print "\t%lf"%((len(mask)-np.argmin(np.apply_along_axis(lambda x: sum(x),axis=0,arr=mask.T[i:i+win])))/(1.0*len(mask)))
        x.append(((i + win / 2.0) / len(mask.T)))
        y.append(((len(mask) - np.argmin(np.apply_along_axis(lambda x: sum(x), axis=0, arr=mask.T[i:i + win]))) / (
        1.0 * len(mask))))
    return pd.DataFrame(data=y, index=x, columns=["values"])


def valid_date(s):
    try:
        return pd.to_datetime(s)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def get_byte_multiplier(s):
    values_prefix={"T":10**12,"G":10**9,"M":10**6,"K":10**3}
    values_bytes={"B":8,"b":1}
    if len(s)==2:
        return values_prefix[s[0].upper()]*values_bytes[s[1]]
    elif s[0] in values_prefix.keys():
        return values_prefix[s[0]]*values_bytes["b"]
    elif s[0] in values_bytes.keys():
        return values_bytes[s[0]]
    raise ValueError


def valid_bitcount(s):
    try:
        return float(s)
    except ValueError:
        match=re.findall("([0-9\.]*) *([GMKgmk]?[Bb]?)[(?:ps)(?:PS)]?",s)[0]
        return float(match[0])*get_byte_multiplier(match[1])



def scale_data_to_date(df, ref_date, observation_time_span=pd.Timedelta("1D")):
    '''
    :param df: the dataframe to scale
    :param ref_date: the date of the begining of the observation window
    :param observation_time_span: a time delta representing the lenght of the observations
    :return:
    '''
    index = []
    for key, value in enumerate(df.index):
        index.append(ref_date + observation_time_span * value)
        # dump the ts
    ts = pd.Series(df["values"].values, index=index)
    return ts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', "-f", type=str, required=True)
    parser.add_argument('--date', "-d", required=True, type=valid_date)
    parser.add_argument('--maxY', "-y", required=True, type=valid_bitcount,help="maximum quantity of bytes in the Y axis")
    args = parser.parse_args()

    df = extract_data_from_graph(args.file)
    df = scale_data_to_date(df, args.date)
    df=df*args.maxY
    df.to_csv(sys.stdout)
