#!/usr/bin/env python
import argparse
import logging
from functools import partial

import matplotlib

matplotlib.use('Agg')

import multiprocessing
from offline.pricing.generator import price_slas, p
from offline.time.simu_time import do_simu

parser = argparse.ArgumentParser(description='launch time simu')
parser.add_argument('--ispmigration', '-i', default=10, type=float)
parser.add_argument('--cdnDiscount', '-d', default=0.5, type=float)
parser.add_argument('--threads', '-t', default=(multiprocessing.cpu_count() - 1), type=int)
parser.add_argument('--log', '-l', default="DEBUG", type=str)

args = parser.parse_args()

numeric_level = getattr(logging, args.log.upper(), None)
if numeric_level is None:
    numeric_level = logging.INFO

best_discretization_param_str, isp_cost, total_bw, total_sla_price, sla_count = do_simu(
    migration_costs_func=lambda x: sum([10 + abs(y[0] - y[1]) for y in x]) * args.ispmigration,
    sla_pricer=partial(price_slas, f=partial(p, r=args.cdnDiscount, m=24)), loglevel=numeric_level,
    threads=args.threads)

print("migration_cos\t\tcdn_discount\t\tbest_discretization_param_str\t\tisp_cost\t\ttotal_bw=\t\ttotal_sla_price=\t\tsla_count=%d" )
print(("%lf\t\t%lf\t\t%s\t\t%lf\t\t%lf\t\t%lf\t\t%d" % (
args.ispmigration,
args.cdnDiscount,
best_discretization_param_str,
isp_cost,
total_bw,
total_sla_price,
sla_count)))
