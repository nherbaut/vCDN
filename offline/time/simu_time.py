#!/usr/bin/env python
import sys

import numpy as np
import pandas as pd

from ..core.service import Service
from ..core.sla import findSLAByDate
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
su = Substrate.fromGrid(delay=10, cpu=50)

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
tenant_start_count=rs.randint(low=2, high=5)
tenant_cdn_count=rs.randint(low=1, high=3)
draw=rs.choice(su.nodes, size=tenant_start_count+tenant_cdn_count, replace=False)
tenant_start_nodes =draw[:tenant_start_count]
tenant_cdn_nodes = draw[tenant_start_count:]

# fill the db with some data
# fill_db_with_sla()
# fill_db_with_sla(tenant, substrate=su)
ts, date_start, date_start_forecast, date_end_forecast = fill_db_with_sla(tenant, start_nodes=tenant_start_nodes,
                                                                          cdn_nodes=tenant_cdn_nodes, substrate=su,
                                                                          delay=200)
ts, date_start, date_start_forecast, date_end_forecast = fill_db_with_sla(tenant, start_nodes=tenant_start_nodes,
                                                                          cdn_nodes=tenant_cdn_nodes, substrate=su,
                                                                          delay=200)

current_slas = []
# for each our
for adate in pd.date_range(date_start_forecast, date_end_forecast, freq="H"):

    aslas_for_date = findSLAByDate(adate)
    new_slas = [sla for sla in aslas_for_date if sla not in current_slas]
    expired_slas = [sla for sla in current_slas if sla not in aslas_for_date]
    current_slas = [sla for sla in current_slas if sla not in expired_slas]

    # remove expired services
    for sla in expired_slas:
        service = Service.getFromSla(sla)
        su.release_service(service)
        session.delete(service)
        session.commit()

    # create the services and solve it.
    for sla in new_slas:
        service = Service([sla])
        service.solve()
        session.commit()
        if service.mapping is not None:
            su.consume_service(service)
            current_slas.append(sla)

    print("for date %s we have %d slas (%s) with total bw= %lf with a total of %lf cost"%(adate,len(current_slas)," ".join([str(sla.id) for sla in current_slas]), sum([sla.bandwidth for sla in current_slas]),  sum([sla.services[0].mapping.objective_function for sla in current_slas])))

