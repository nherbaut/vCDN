import re
import subprocess
import os
from mapping import Mapping

def shortest_path(node1,node2):
    with open("node1.data","w") as f:
        f.write("%s\n"%node1)
    with open("node2.data","w") as f:
        f.write("%s\n"%node2)

    subprocess.call(["scip", "-b", "./sp.batch"],stdout=open(os.devnull, 'wb'))
    with open("solutions.data", "r") as sol:
        data = sol.read()
        data = data.split("\n")

    for line in data:
        matches = re.findall("^objective value: *([0-9\.]*)$",line)
        if (len(matches) > 0):
            return float(matches[0])

    return None

def solve(service, substrate,allow_violations=False):
    service.write()
    substrate.write()
    violations=[]

    if not allow_violations:
        subprocess.call(["scip", "-b", "./scpi.batch"],stdout=open(os.devnull, 'wb'))
    else:
        subprocess.call(["scip", "-b", "./scpi-debug.batch"],stdout=open(os.devnull, 'wb'))
    # plotting.plotsol()
    # os.subprocess.call(["cat", "./substrate.dot", "|", "dot", "-Tpdf", "-osol.pdf"])
    with open("solutions.data", "r") as sol:
        data = sol.read()
        if "infeasible" in data or "no solution" in data:
            return None

        data = data.split("\n")
        nodesSol = []
        edgesSol = []
        objective_function=None
        for line in data:
            matches = re.findall("^x\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                nodesSol.append(matches[0])
                continue
            matches = re.findall("^y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                edgesSol.append(matches[0])
                continue
            matches = re.findall("^objective value: *([0-9\.]*)$",line)
            if (len(matches) > 0):
                objective_function=float(matches[0])
                continue

            matches = re.findall("^(.*)_master",line)
            if (len(matches) > 0):
                violations.append(matches[0])
                continue

        return Mapping(nodesSol, edgesSol,objective_function,violations=violations)
