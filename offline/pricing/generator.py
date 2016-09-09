import csv
import os
from functools import partial

import numpy as np
import pandas as pd

PRICING_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../pricing')


def migration_calculator(x):
    return sum([abs(y[0] - y[1]) for y in x]) * 10


def get_migration_calculator(spec_file=os.path.join(PRICING_FOLDER, "vmg/vio_vmg_pricing_aws.properties")):
    # with open(spec_file, "r") as f:
    #    for key in csv.reader(filter(lambda row: row[0] != '#', f)):
    #        return eval(key[0])
    return migration_calculator


def get_vmg_calculator(sys_spec_file_path=os.path.join(PRICING_FOLDER, "vmg/vio_vmg_pricing_aws.properties")):
    '''
    :param sys_spec_file_path: specs for vmg pricing
    :return: a function used to compute vmh price according to prop file
    '''

    sys_specs = None
    with open(sys_spec_file_path, "r") as f:
        for key in csv.reader(filter(lambda row: row[0] != '#', f)):
            return eval(key[0])


def get_vcdn_calculator(file_path="cdn/azure_cdn_pricing_zone1.properties"):
    '''

    :param file_path: specs for cdn pricing
    :return: return a function used to compute cdn price according to porperties file
    '''
    threshold_prices = {}
    with open(file_path, "r") as f:
        for key, value in csv.reader(filter(lambda row: row[0] != '#', f), delimiter=","):
            threshold_prices[key] = value

    return partial(vcdn_calculator, threshold_prices=threshold_prices)


def vmg_calculator(bandwidth_bps, sys_spec, net_spec):
    return bandwidth_bps / net_spec


def vcdn_calculator(quantity_gb, threshold_prices):
    '''

    :param quantity_gb: the quantity of bytes to get the the pricing from
    :param threshold_prices: specs for pricing
    :return: a price in USD
    '''
    res = 0
    for threshold, price in threshold_prices.items():
        if (quantity_gb >= threshold):
            res += 10 * 0.087
            quantity_gb -= threshold
        else:
            res += quantity_gb * 0.087
            break
    return res


def p(t, r, m):
    assert (t >= 0)
    return r if t > m else np.exp(t * np.log(r) / m)


def price_slas(slas, f=partial(p, r=0.40, m=24)):
    prices = []
    for sla in slas:
        prices.append(price_sla(sla[0], sla.index[0], sla.index[-1],  f=f))
    return sum(prices)


def price_sla(bw, date_start, date_end,  f):
    hours = 1+(date_end - date_start).value / (10 ** 9 * 3600.0)
    if hours == 0:
        print("what?")
        return 0

    price = bw * f(hours) * hours
    return price
