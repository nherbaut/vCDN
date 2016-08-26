#!/usr/bin/env python
import collections
import sys

import numpy as np
import pandas as pd

from ..core.service import Service
from ..core.sla import findSLAByDate, Sla
from ..core.substrate import Substrate
from ..time.namesgenerator import get_random_name
from ..time.persistence import *
from ..time.slagen import fill_db_with_sla

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


def solve_optim(sla, substrate):
    '''
    solve optimally the provided sla given the substrate
    :param sla:
    :param substrate:
    :return:
    '''

    best_service = None
    best_mapping = None
    best_price = sys.maxint
    for vmg in range(1, len(sla.get_start_nodes()) + 1):
        for vcdn in range(1, vmg + 1):
            service = Service([sla], vmg, vcdn)
            m = service.solve()

            if (m is not None and m.objective_function < best_price):
                best_price = m.objective_function
                best_service = service
                best_mapping = m

    if best_service is None:
        raise ValueError
    else:
        return best_service, best_mapping


Base.metadata.create_all(engine)
rs = np.random.RandomState(1)
# clear the db
drop_all()

# create the topo and load it
su = Substrate.fromGrid(delay=10,cpu=50)

for node in su.nodes:
    session.add(node)
session.commit()
for edge in su.edges:
    session.add(edge)
session.commit()
session.add(su)
session.commit()

tenant = Tenant(name=get_random_name())
session.add(tenant)
session.commit()
tenant_start_nodes = rs.choice(su.nodes, size=rs.randint(low=2, high=3), replace=False)
tenant_cdn_nodes = rs.choice(su.nodes, size=rs.randint(low=1, high=2), replace=False)

# fill the db with some data
# fill_db_with_sla()
# fill_db_with_sla(tenant, substrate=su)
ts, date_start, date_start_forecast, date_end_forecast = fill_db_with_sla(tenant, start_nodes=tenant_start_nodes,
                                                                          cdn_nodes=tenant_cdn_nodes, substrate=su,
                                                                          delay=200)
ts, date_start, date_start_forecast, date_end_forecast = fill_db_with_sla(tenant, start_nodes=tenant_start_nodes,
                                                                          cdn_nodes=tenant_cdn_nodes, substrate=su,
                                                                          delay=200)


timeline_old = collections.defaultdict(lambda: [])
timeline_new = collections.defaultdict(lambda: [])
for adate in pd.date_range(date_start_forecast, date_end_forecast, freq="H"):
    total_bw = 0


    slas = findSLAByDate(adate)

    for sla in slas:
        service = Service([sla])
        service.solve()
        session.commit()
        if service.mapping is not None:
            print "sla %d consumed %lf " % (sla.id,service.mapping.objective_function)
            #su.consume_service(service)
        else:
            print "can't consume unmapped service"


    service = Service(slas)
    service.solve()
    session.commit()
    if service.mapping is not None:
        print "alltogether they consumed %lf " % (service.mapping.objective_function)
        #su.consume_service(service)

    raw_input("...")
    timeline_old = timeline_new
