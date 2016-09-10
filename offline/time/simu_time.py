#!/usr/bin/env python
import logging
import os
import sys

import numpy as np
import pandas as pd

from ..core.mapping import Mapping
from ..core.service import Service
from ..core.sla import findSLAByDate
from ..core.substrate import Substrate
from ..pricing.generator import migration_calculator
from ..pricing.generator import price_slas
from ..time.namesgenerator import get_random_name
from ..time.persistence import engine, drop_all, Base, Session, Tenant
from ..time.slagen import fill_db_with_sla
from ..tools.candelPlot import candelPlot

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')
DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')

rs = np.random.RandomState(1)


# Print iterations progress
def printProgress(iteration, total, prefix='', suffix='', decimals=1, barLength=100, file=sys.stderr):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    formatStr = "{0:." + str(decimals) + "f}"
    percents = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = 'X' * filledLength + '-' * (barLength - filledLength)
    file.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    file.flush()
    if iteration == total:
        file.write('\n')
        file.flush()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def yellow(arg):
    return col(arg, bcolors.WARNING)


def red(arg):
    return col(arg, bcolors.FAIL)


def green(arg):
    return col(arg, bcolors.OKGREEN)


def col(arg, colr=bcolors.ENDC):
    return colr + str(arg) + bcolors.ENDC


def merge_services(s1, s2, migration_costs_func):
    '''

    :param s1: a service with a mapping
    :param s2: a service with a mapping
    :return: the merged Service if the cost is lower, None otherwize
    '''
    session = Session()
    assert s1.mapping is not None
    assert s2.mapping is not None
    logging.info("TRY MERGING %s with %s" % (s1, s2))
    s3 = Service.get_optimal(s1.slas + s2.slas)

    if s3 is not None and s3.mapping is not None:
        consolidated_cost = s3.mapping.objective_function + Mapping.get_migration_cost(s3.mapping, s1.mapping,
                                                                                       migration_costs_func)
        individual_costs = s2.mapping.objective_function + s1.mapping.objective_function
        logging.debug("CONSOLIDATED COSTS for %s : %lf" % (s3, s3.mapping.objective_function))
        logging.debug("INDIVIDUAL COSTS FOR %s : %lf" % ("\t".join([str(s1), str(s2)]), individual_costs))
        if consolidated_cost < individual_costs:
            logging.debug("CREATED %s AND OPTIMAL" % s3)
            session.flush()
            return s3, Mapping.get_migration_cost(s3.mapping, s1.mapping, migration_costs_func)
        else:
            logging.debug("CREATED %s BUT SUBOPTIMAL" % s3)
            session.delete(s3)
    session.flush()
    return None, None


def do_simu(migration_costs_func=migration_calculator, sla_pricer=price_slas, loglevel=logging.INFO):
    logging.basicConfig(filename='simu.log', level=loglevel)

    Base.metadata.create_all(engine)
    # clear the db
    drop_all()

    session = Session()
    # create the topo and load it
    su = Substrate.fromGrid(delay=2, cpu=10000000, bw=10 ** 12)

    session.add(su)
    session.flush()

    tenant = Tenant(name=get_random_name())
    session.add(tenant)
    session.flush()

    for i in range(0, 1):
        tenant_start_count = rs.randint(low=5, high=6)
        tenant_cdn_count = rs.randint(low=2, high=3)
        draw = rs.choice(su.nodes, size=tenant_start_count + tenant_cdn_count, replace=False)
        tenant_start_nodes = draw[:tenant_start_count]
        tenant_cdn_nodes = draw[tenant_start_count:]

        # fill the db with some data
        # fill_db_with_sla()
        # fill_db_with_sla(tenant, substrate=su)
        data_files = [file for file in os.listdir(DATA_FOLDER) if
                      "daily" in file and not file.startswith(".") and file.endswith(".csvx")]
        rs.shuffle(data_files)
        # print("using : %s" % (" ".join([file for file in data_files])))
        date_start_forecast, date_end_forecast, total_sla_price, best_discretization_parameter, sla_count = fill_db_with_sla(
            data_files, sla_pricer, tenant,
            start_nodes=tenant_start_nodes,
            cdn_nodes=tenant_cdn_nodes, substrate=su,
            delay=100, rs=rs,
        )

        session.flush()

        current_services = []
        isp_cost = 0
        # for each our

        data = []
        total_bandwidth = sys.float_info.max
        date_counter = 0
        printProgress(date_counter, len(pd.date_range(date_start_forecast, date_end_forecast, freq="H")),
                      prefix='Progress:', suffix='Complete', barLength=50)
        for adate in pd.date_range(date_start_forecast, date_end_forecast, freq="H"):
            date_counter += 1
            printProgress(date_counter, len(pd.date_range(date_start_forecast, date_end_forecast, freq="H")),
                          prefix='Progress:', suffix='Complete', barLength=50)
            active_service = []
            actives_sla = findSLAByDate(adate)
            legacy_slas = []

            active_sla_in_current_services = []
            for service in session.query(Service).all():
                active_sla_in_current_services += service.slas

            active_sla_in_current_services = sorted(active_sla_in_current_services, key=lambda x: x.id)
            new_slas = [sla for sla in actives_sla if sla not in active_sla_in_current_services]
            slas_pending_removal = [sla for sla in active_sla_in_current_services if sla not in actives_sla]
            stay_in_place_slas = [sla for sla in active_sla_in_current_services if sla in actives_sla]

            bw_new_slas = sum([sla.get_total_bandwidth() for sla in new_slas])
            bw_removed_slas = sum([sla.get_total_bandwidth() for sla in slas_pending_removal])

            logging.info("SLAS:%s %s %s" % (" ".join([str(s.id) for s in stay_in_place_slas]),
                                            green(" ".join([str(s.id) for s in new_slas])),
                                            red(" ".join([str(s.id) for s in slas_pending_removal]))))

            # for each service
            for current_service in session.query(Service).all():

                # check if all slas are still active
                if all([s in actives_sla for s in current_service.slas]):
                    logging.info("SLA STILL PRESENT %s" % current_service)
                    active_service.append(current_service)
                    legacy_slas += current_service.slas

                else:  # at least one SLA is removed
                    # as least one remaining?
                    if any([s in actives_sla for s in current_service.slas]):
                        removed_slas = [str(s.id) for s in current_service.slas if s not in actives_sla]
                        logging.info("UPDATED %s REMOVED [%s]" % (current_service, removed_slas))

                        su.release_service(current_service)
                        current_service.slas = [s for s in current_service.slas if s in actives_sla]
                        session.flush()
                        current_service.update_mapping()
                        su.consume_service(current_service)
                        legacy_slas += current_service.slas

                    else:  # none remaining, we have to delete the service
                        logging.info("DELETED %d" % current_service.id)
                        su.release_service(current_service)
                        session.delete(current_service)
                        session.flush()

            new_slas = [s for s in actives_sla if s not in legacy_slas]
            total_migration_costs = 0

            if len(new_slas) > 0:

                new_slas_service = Service.get_optimal([s for s in actives_sla if s not in legacy_slas])

                cost_non_migrated = sum(
                    [service.mapping.objective_function for service in session.query(Service).all()])

                # for each already embeded service, try to merge recursively
                merged_service = new_slas_service
                for service in sorted([service for service in session.query(Service).all()],
                                      key=lambda service: len(service.slas)):
                    # if already merged, or common slas
                    if len(set(service.slas) & set(merged_service.slas)) > 0:
                        continue
                    merged_service_res, migration_costs = merge_services(service, merged_service, migration_costs_func)
                    # merged_service_res, migration_costs = None, None
                    if migration_costs is not None:
                        total_migration_costs += migration_costs
                    if merged_service_res is not None:
                        logging.info("DELETE: %s" % red(str(service)))
                        session.delete(service)
                        logging.info("DELETE: %s" % red(str(merged_service)))
                        session.delete(merged_service)
                        logging.info("CREATED: %s" % green(str(merged_service_res)))
                        merged_service = merged_service_res
                        session.add(merged_service)
                        logging.debug(
                            "%s is merged with %s, result: %s" % (service, merged_service, merged_service_res))
                        session.flush()
                    else:
                        logging.debug("%s can't be merged with %s" % (service, merged_service))

                if merged_service.mapping is None:
                    logging.info("CAN'T EMBED SERVICE")
                    session.delete(merged_service)
                    session.flush()
                else:
                    session.flush()
                    su.consume_service(merged_service)
                    logging.info("CREATION SUCCESSFUL")
            else:
                # no new sla => no migration cost
                cost_non_migrated = isp_cost

            isp_cost = sum([service.mapping.objective_function for service in session.query(Service).all()])

            logging.warning(
                "ISP cost: %lf (migration : %lf)" % (isp_cost + total_migration_costs, total_migration_costs))

            data.append(
                (isp_cost, cost_non_migrated, bw_new_slas / total_bandwidth, bw_removed_slas / total_bandwidth,
                 total_bandwidth))
            logging.info(("SERVICES:\n%s" % yellow(("\n".join([str(s) for s in list(session.query(Service).all())])))))
            logging.info("SUBSTRATE: %s" % su)
            total_bandwidth = max(1, sum(
                [sum([sla.get_total_bandwidth() for sla in service.slas]) for service in session.query(Service).all()]))

        y, y1, sla_hi, sla_low, ttbw = zip(*data)
        # print("[")
        # for i in range(0, len(y)):
        #    print("(%lf,%lf,%lf,%lf)," % (y[i], y1[i], sla_hi[i], sla_low[i]))
        # print("]")
        candelPlot(np.arange(0, len(y)), y, y1, sla_hi, sla_low)
        print("%s,%lf,%lf,%lf,%d" % (
            str(best_discretization_parameter), sum([x[0] for x in data]), sum(ttbw[1:]), total_sla_price, sla_count))
