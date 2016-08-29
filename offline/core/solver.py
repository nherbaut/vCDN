import os
import re
import subprocess

from sqlalchemy import or_, and_

from ..core.mapping import Mapping
from ..time.persistence import  session, Edge, ServiceEdge, ServiceNode, NodeMapping, EdgeMapping
from sqlalchemy.orm.exc import NoResultFound
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
                try:
                    node_id = matches[0][0]
                    snode_id, service_id, sla_id = matches[0][1].split("_")
                    service_node_id = session.query("ServiceNode.id").filter(
                        and_(ServiceNode.sla_id == sla_id, ServiceNode.service_id == service_id,
                             ServiceNode.node_id == snode_id)).one()[0]
                    nodeMapping = NodeMapping(node_id=node_id, service_node_id=service_node_id,service_id=service_id,sla_id=sla_id)
                    nodesSols.append(nodeMapping)

                    continue
                except NoResultFound as e:
                    print e

            # search edge
            matches = re.findall("^y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                node_1, node_2, snode_1, snode_2 = matches[0]
                snode_1, service_id, sla_id = snode_1.split("_")
                snode_2, service_id, sla_id = snode_2.split("_")
                session.query()

                edge_id = session.query(Edge.id).filter(or_(and_(Edge.node_1 == node_1, Edge.node_2 == node_2),
                                                            and_(Edge.node_1 == node_2, Edge.node_2 == node_1))).one()[0]
                snode_1_id = session.query(ServiceNode.id).filter(
                    and_(ServiceNode.sla_id == sla_id, ServiceNode.service_id == service_id,
                         ServiceNode.node_id == snode_1)).one()[0]
                snode_2_id = session.query(ServiceNode.id).filter(
                    and_(ServiceNode.sla_id == sla_id, ServiceNode.service_id == service_id,
                         ServiceNode.node_id == snode_2)).one()[0]
                sedge_id = session.query(ServiceEdge.id).filter(
                    and_(ServiceEdge.node_1_id == snode_1_id, ServiceEdge.node_2_id == snode_2_id,
                         ServiceEdge.service_id == service_id, ServiceEdge.sla_id == sla_id)).one()[0]

                edgeMapping = EdgeMapping(edge_id=edge_id, serviceEdge_id=sedge_id)
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
    service.write()
    substrate.write()
    session.flush()
    mapping=solve_inplace()
    service.mapping=mapping
    session.add(mapping)
    session.flush()




