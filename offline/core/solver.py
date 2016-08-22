import copy
import os
import re
import subprocess
import sys

from ..core.mapping import Mapping
from ..core.service import Service

OPTIM_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../optim')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')





def solve_inplace(allow_violations=False, preassign_vhg=False):
    '''
    solve without rewriting intermedia files
    :return: a mapping
    '''

    violations = []
    if not allow_violations:
        if not preassign_vhg:  # run the optim without CDNs
            subprocess.call(["scip", "-c", "read %s" % os.path.join(OPTIM_FOLDER, "optim.zpl"), "-c", "optimize ", "-c",
                             "write solution %s" % (os.path.join(RESULTS_FOLDER, "solutions.data")), "-c", "q"],
                            stdout=open(os.devnull, 'wb'))
        else:  # run the optim with CDN using reoptim
            subprocess.call(["scip", "-c", "read %s" % os.path.join(OPTIM_FOLDER, "optim.zpl"), "-c",
                             "read %s" % os.path.join(RESULTS_FOLDER, "initial.sol"), "-c",
                             "set reoptimization enable true", "-c", "optimize ", "-c",
                             "write solution %s" % (os.path.join(RESULTS_FOLDER, "solutions.data")), "-c", "q"],
                            stdout=open(os.devnull, 'wb'))

    else:
        subprocess.call(["scip", "-c", "read %s" % os.path.join(OPTIM_FOLDER, "optim.zpl"), "-c", "optimize ", "-c",
                         "write solution %s" % (os.path.join(RESULTS_FOLDER, "solutions.data")), "-c", "q"],
                        stdout=open(os.devnull, 'wb'))
    # plotting.plotsol()
    # os.subprocess.call(["cat", "./substrate.dot", "|", "dot", "-Tpdf", "-osol.pdf"])
    with open(os.path.join(RESULTS_FOLDER, "solutions.data"), "r") as sol:
        data = sol.read()
        if "infeasible" in data or "no solution" in data:
            return None

        data = data.split("\n")
        nodesSol = []
        edgesSol = []
        objective_function = None
        for line in data:
            matches = re.findall("^x\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                nodesSol.append(matches[0])
                continue
            matches = re.findall("^y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                edgesSol.append(matches[0])
                continue
            matches = re.findall("^objective value: *([0-9\.]*)$", line)
            if (len(matches) > 0):
                objective_function = float(matches[0])
                continue

            matches = re.findall("^(.*)_master", line)
            if (len(matches) > 0):
                violations.append(matches[0])
                continue

        return Mapping(nodesSol, edgesSol, objective_function, violations=violations)


def solve(service, substrate, allow_violations=False, smart_ass=False, preassign_vhg=True):
    if preassign_vhg:
        service_no_cdn = copy.deepcopy(service)
        service_no_cdn.max_cdn_to_use = 0
        service_no_cdn.cdn = []
        mapping = solve(service_no_cdn, substrate, allow_violations=False, smart_ass=smart_ass, preassign_vhg=False)
        if mapping is None:
            return None
        service.vhg_hints = mapping.get_vhg_mapping()

    service.write()
    substrate.write()

    return solve_inplace(allow_violations, preassign_vhg)


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
    for vmg in range(1, len(sla.start)+1):
        for vcdn in range(1, vmg+1):
            service = Service.fromSla(sla)
            service.vcdncount = vcdn
            service.vhgcount = vmg
            m = solve(service, substrate, smart_ass=True)
            if (m.objective_function < best_price):
                best_price = m.objective_function
                best_service = service
                best_mapping=m

    if best_service is None:
        raise ValueError
    else:
        return best_service,best_mapping
