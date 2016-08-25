import copy
import os
import re
import subprocess
import sys

from ..core.mapping import Mapping
from ..time.persistence import NodeMapping, EdgeMapping, session, Edge, ServiceEdge

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
        nodesSols = []
        edgesSol = []
        objective_function = None
        for line in data:

            # search node
            matches = re.findall("^x\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                nodeMapping = NodeMapping(node_id=matches[0][0], service_node_id=matches[0][1])
                nodesSols.append(nodeMapping)
                continue

            # search edge
            matches = re.findall("^y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                node_1, node_2, snode_1, snode_2 = matches[0]
                edge_id= session.query(Edge.id).filter(Edge.node_1 == node_1).filter(Edge.node_2 == node_2).one()
                sedge_id= session.query(ServiceEdge.id).filter(ServiceEdge.node_1 == snode_1).filter(
                    ServiceEdge.node_2 == snode_2).one()
                edgeMapping = EdgeMapping(edge_id=sedge_id, service_edge_id=sedge_id)
                edgesSol.append(edgeMapping)
                continue
            matches = re.findall("^objective value: *([0-9\.]*)$", line)
            if (len(matches) > 0):
                objective_function = float(matches[0])
                continue

            matches = re.findall("^(.*)_master", line)
            if (len(matches) > 0):
                violations.append(matches[0])
                continue
        mapping = Mapping(node_mappings=nodesSols, edge_mappings=edgesSol, objective_function=objective_function)
        return mapping


def solve(service, substrate):

    service.write(cdn=False)
    substrate.write()
    return solve_inplace()



