#!/usr/bin/env python
import argparse
import logging
from functools import partial
import matplotlib
matplotlib.use('Agg')





from offline.pricing.generator import price_slas, p
from offline.time.simu_time import do_simu

parser = argparse.ArgumentParser(description='launch time simu')
parser.add_argument('--ispmigration', '-i', default=10, type=float)
parser.add_argument('--cdnDiscount', '-d', default=0.5, type=float)
parser.add_argument('--log', '-l', default="DEBUG", type=str)

args = parser.parse_args()

numeric_level = getattr(logging, args.log.upper(), None)
if numeric_level is None:
    numeric_level = logging.INFO


a,b,c,d,e = do_simu(migration_costs_func=lambda x: sum([abs(y[0] - y[1]) for y in x]) * args.ispmigration,
        sla_pricer=partial(price_slas, f=partial(p, r=args.cdnDiscount, m=24)), loglevel=numeric_level)

print("%lf,%lf,%s,%lf,%lf,%lf,%d" % (args.ispmigration,args.cdnDiscount,a,b,c,d,e))
