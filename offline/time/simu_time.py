#!/usr/bin/env python
import logging
import sys

import numpy as np
import pandas as pd

from ..core.sla import Sla
from ..core.service import Service
from ..core.sla import findSLAByDate
from ..core.substrate import Substrate
from ..time.namesgenerator import get_random_name
from ..time.persistence import *
from ..time.slagen import fill_db_with_sla

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

logging.basicConfig(level=logging.INFO)


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

cpuCost = 2000
netCost = 20000.0 / 10 ** 9
# create the topo and load it
su = Substrate.fromGrid(delay=10, cpu=50, cpuCost=cpuCost, netCost=netCost)

for node in su.nodes:
    session.add(node)
    session.flush()

for edge in su.edges:
    session.add(edge)
    session.flush()

session.add(su)
session.flush()

tenant = Tenant(name=get_random_name())
session.add(tenant)
session.flush()

for i in range(0, 1):
    tenant_start_count = rs.randint(low=2, high=5)
    tenant_cdn_count = rs.randint(low=1, high=3)
    draw = rs.choice(su.nodes, size=tenant_start_count + tenant_cdn_count, replace=False)
    tenant_start_nodes = draw[:tenant_start_count]
    tenant_cdn_nodes = draw[tenant_start_count:]

    # fill the db with some data
    # fill_db_with_sla()
    # fill_db_with_sla(tenant, substrate=su)
    ts, date_start, date_start_forecast, date_end_forecast = fill_db_with_sla(tenant, start_nodes=tenant_start_nodes,
                                                                              cdn_nodes=tenant_cdn_nodes, substrate=su,
                                                                              delay=200)

session.flush()

current_services = []
# for each our


for adate in pd.date_range(date_start_forecast, date_end_forecast, freq="H"):
    active_service = []
    actives_sla = findSLAByDate(adate)
    legacy_slas = []
    logging.info("SLAS:%s" % (" ".join([str(s.id) for s in actives_sla])))
    logging.info(("SERVICES:%s" % ("\t ".join([str(s) for s in list(session.query(Service).all())]))))
    logging.info("SUBSTRATE: %s" % su)
    # for each service

    for current_service in session.query(Service).all():

        # check if all slas are still active
        if all([s in actives_sla for s in current_service.slas]):
            logging.info("KEEP %s" % current_service)
            active_service.append(current_service)
            legacy_slas += current_service.slas

        else:  # at least one SLA is removed
            # as least one remaining?
            if any([s in actives_sla for s in current_service.slas]):
                removed_slas = [str(s.id) for s in current_service.slas if s not in actives_sla]
                logging.info("UPDATED %s REMOVED [%s]" % (current_service, removed_slas))

                logging.info("service has %d mapped nodes and %d mapped edges" % (
                    len(current_service.serviceNodes), len(current_service.serviceEdges)))
                su.release_service(current_service)
                current_service.slas = [s for s in current_service.slas if s in actives_sla]
                current_service.update_mapping()
                session.flush()
                su.consume_service(current_service)
                session.flush()
                legacy_slas += current_service.slas
                logging.info("service has %d mapped nodes and %d mapped edges" % (
                    len(current_service.serviceNodes), len(current_service.serviceEdges)))

            else:  # none remaining, we have to delete the service
                logging.info("DELETED %d" % current_service.id)
                session.delete(current_service)
                su.release_service(service)
                session.flush()

    new_slas = [s for s in actives_sla if s not in legacy_slas]
    if len(new_slas) > 0:
        service = Service([s for s in actives_sla if s not in legacy_slas])
        session.add(service)
        logging.info("CREATE %s" % service)
        session.flush()
        service.solve()
        su.consume_service(service)
        if service.mapping is not None:
            logging.info("CREATION SUCCESSFUL")
        else:
            exit(-1)

        session.flush()
