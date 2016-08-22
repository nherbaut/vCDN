#!/usr/bin/env python
import collections

import numpy as np
import pandas as pd

from ..core.sla import findSLAByDate
from ..core.sla import Sla
from ..core.solver import solve_optim
from ..core.substrate import Substrate
from ..time.persistence import *
from ..time.slagen import fill_db_with_sla

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

# clear the db
drop_all()

# fill the db with some data
# fill_db_with_sla()
# fill_db_with_sla()
ts, date_start, date_start_forecast, date_end_forecast = fill_db_with_sla()

rs = np.random.RandomState(0)

su = Substrate.fromGrid()

random_nodes = rs.choice(su.nodesdict.keys(), size=100)


timeline_old = collections.defaultdict(lambda: [])
timeline_new = collections.defaultdict(lambda: [])
for adate in pd.date_range(date_start_forecast, date_end_forecast, freq="H"):
    total_bw = 0
    DBslas = findSLAByDate(adate)
    for dbSla in DBslas:
        if dbSla in timeline_old:
            print "welcome back!"
        sla = Sla.fromDBSLA(dbSla)
        sla.start = rs.choice(su.nodesdict.keys(), size=rs.randint(low=1, high=1), replace=False)
        sla.cdn = rs.choice(su.nodesdict.keys(), size=rs.randint(low=1, high=1), replace=False)
        sla.max_cdn_to_use = len(sla.cdn)
        sla.delay = 50
        service, mapping = solve_optim(sla, su)
        su.consume_service(service, mapping)
        timeline_new[dbSla].append((service, mapping))
    timeline_old=timeline_new


