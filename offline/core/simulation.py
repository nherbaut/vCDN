import logging
import sys
from copy import deepcopy

import numpy as np
import substrate
import utils
from result import ResultItem
from service import Service
from sla import generate_random_slas
from solver import solve


@utils.timed
def do_simu(**kwargs):
    '''

    :param relax_vhg: True|False  : do we add vhg?
    :param relax_vcdn:  True|False: do we add vcdn?
    :param seed:  what is the random seed
    :param sla_count: how many sla to generate?
    :param rejected_threshold:  stop after X rejection
    :param iteration_threshold:  stop after Y iteration
    :param smart_ass: use heuristics to groups S to VHG and vCDN to VHG
    :param sorted: use sorted SLA
    :return: a list containing each step results
    '''

    count_transformation = 0

    result = []
    cost_function = []
    rejected = 0
    rs = np.random.RandomState(seed=kwargs["seed"])

    su = substrate.get_substrate(rs)
    # su=Substrate.fromSpec(5,5,10**10,1,100)
    su.cpuCost = kwargs["cpuCost"]
    su.netCost = kwargs["netCost"]

    # su=Substrate.fromSpec(5,5,8**9,30,50)
    su.write()
    if "sorted" in kwargs and kwargs["sorted"] == True:
        slas = sorted(generate_random_slas(rs, su, kwargs["sla_count"]), key=lambda x: -x.bandwidth)
    else:
        slas = generate_random_slas(rs, su, kwargs["sla_count"])

    result.append(ResultItem(deepcopy(su), 0, 0, None, None))

    relax_vhg = kwargs["relax_vhg"]
    relax_vcdn = kwargs["relax_vcdn"]

    while (kwargs["rejected_threshold"] > 0 and rejected < kwargs["rejected_threshold"]) or (
                    kwargs["iteration_threshold"] > 0 and (
                    kwargs["sla_count"] - len(slas) < kwargs["iteration_threshold"])):
        best_objective_function = None
        best_mapping = None
        count_transformation_loop = 0
        sla = slas.pop()
        service = Service.fromSla(sla)
        service.spvhg = kwargs["smart_ass"]
        mapping = None
        mapping_res = []

        if relax_vhg:
            vhg_max = len(service.start)
        else:
            vhg_max = 1

        if relax_vcdn:
            if relax_vhg:
                vcdn_max = vhg_max
            else:
                vcdn_max = len(service.start)
        else:
            vcdn_max = 1

        # run this algo until relaxation is over
        for vhg_count in range(1, vhg_max + 1):
            for vcdn_count in range(1, vcdn_max + 1):

                service.vcdncount = vcdn_count
                service.vhgcount = vhg_count

                logging.debug(
                    "solving for vhg=%d vcdn=%d start=%d" % (service.vhgcount, service.vcdncount, len(service.start)))
                mapping = solve(service, su, smart_ass=kwargs["smart_ass"])
                if mapping is not None:
                    mapping_res.append((deepcopy(service), deepcopy(mapping)))

        accepted_slas = kwargs["sla_count"] - len(slas) - rejected
        if len(mapping_res) == 0:
            rejected += 1
            result.append(ResultItem(deepcopy(su), accepted_slas, float(accepted_slas) / (accepted_slas + rejected),
                                     deepcopy(service), None))
            sys.stdout.write("X")
            continue
        else:
            mapping_res = sorted(mapping_res, key=lambda x: x[1].objective_function)
            for mres in mapping_res:
                logging.debug(
                    "key: %s, %ld" % (str(mres[0].vhgcount) + " " + str(mres[0].vcdncount), mres[1].objective_function))

            service = mapping_res[0][0]
            mapping = mapping_res[0][1]
            logging.debug("winner has %d %d" % (service.vhgcount, service.vcdncount))
            # logging.debug( "winner has %d\t%d" % (service.vhgcount,service.vcdncount))
            su.consume_service(service, mapping)
            su.write()
            result.append(
                ResultItem(deepcopy(su), accepted_slas, float(accepted_slas) / (accepted_slas + rejected),
                           deepcopy(service), deepcopy(mapping)))
            sys.stdout.write("O")
        sys.stdout.flush()

    return result
