import re
import subprocess

from mapping import Mapping


def solve(service, substrate):
    service.write()
    substrate.write()

    subprocess.call(["scip", "-b", "./scpi.batch"])
    # plotting.plotsol()
    # os.subprocess.call(["cat", "./substrate.dot", "|", "dot", "-Tpdf", "-osol.pdf"])
    with open("solutions.data", "r") as sol:
        data = sol.read()
        if "infeasible" in data or "no solution" in data:
            return None
        else:
            data = data.split("\n")
        nodesSol = []
        edgesSol = []
        for line in data:
            matches = re.findall("x\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                nodesSol.append(matches[0])
                continue
            matches = re.findall("y\$(.*)\$(.*)\$(.*)\$([^ \t]+)", line)
            if (len(matches) > 0):
                edgesSol.append(matches[0])
                continue

        return Mapping(nodesSol, edgesSol)
