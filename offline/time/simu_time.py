#!/usr/bin/env python
import collections

import numpy as np
import pandas as pd

from ..core.sla import findSLAByDate
from ..core.solver import solve_optim
from ..core.substrate import Substrate
from ..time.namesgenerator import get_random_name
from ..time.persistence import *
from ..time.slagen import fill_db_with_sla

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

Base.metadata.create_all(engine)
rs = np.random.RandomState(1)
# clear the db
drop_all()

# create the topo and load it
su = Substrate.fromGrid()
for node in su.nodes.keys():
    sn = TopoNode(id=node)
    session.add(sn)

tenant = Tenant(name=get_random_name())
session.add(tenant)
session.commit()
tenant_start_nodes = rs.choice(su.nodes.keys(), size=rs.randint(low=1, high=4), replace=False)
tenant_cdn_nodes = rs.choice(su.nodes.keys(), size=rs.randint(low=1, high=2), replace=False)

# fill the db with some data
# fill_db_with_sla()
# fill_db_with_sla()
ts, date_start, date_start_forecast, date_end_forecast = fill_db_with_sla(tenant, start_nodes=tenant_start_nodes,
                                                                          cdn_nodes=tenant_cdn_nodes)

random_nodes = rs.choice(su.nodes.keys(), size=100)

timeline_old = collections.defaultdict(lambda: [])
timeline_new = collections.defaultdict(lambda: [])
for adate in pd.date_range(date_start_forecast, date_end_forecast, freq="H"):
    total_bw = 0
    slas = findSLAByDate(adate)

    for sla in slas:
        if sla in timeline_old:
            print("welcome back!")

        sla.max_cdn_to_use = len(sla.get_cdn_nodes())
        sla.delay = 50
        session.add(sla)
        session.commit()
        service, mapping = solve_optim(sla, su)
        if mapping is not None:
            mapping.sla = sla
            session.add(mapping)
            session.commit()
            su.consume_service(service, mapping)
            timeline_new[sla].append((service, mapping))
    timeline_old = timeline_new
