import copy
import os
import re
import subprocess

from mapping import Mapping




OPTIM_FOLDER=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../optim')
RESULTS_FOLDER=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../results')

def shortest_path(node1,node2):
    with open(os.path.join(RESULTS_FOLDER,"node1.data"),"w") as f:
        f.write("%s\n"%node1)
    with open(os.path.join(RESULTS_FOLDER,"node2.data"),"w") as f:
        f.write("%s\n"%node2)
    subprocess.call(["scip", "-c", "read %s" % os.path.join(OPTIM_FOLDER,"sp.zpl"),"-c", "read %s" % os.path.join(OPTIM_FOLDER,"sp.zpl"),"-c","optimize ", "-c", "write solution %s" %(os.path.join(RESULTS_FOLDER,"solutions.data")),"-c", "q"],stdout=open(os.devnull, 'wb'))
    #read sp.zpl
    #optimize
    #write solution solutions.data
    #q


    with open(os.path.join(RESULTS_FOLDER,"solutions.data"), "r") as sol:
        data = sol.read()
        data = data.split("\n")

    for line in data:
        matches = re.findall("^objective value: *([0-9\.]*)$",line)
        if (len(matches) > 0):
            return float(matches[0])

    return None

def solve_inplace(allow_violations=False,preassign_vhg=False):
    '''
    solve without rewriting intermedia files
    :return: a mapping
    '''

    violations=[]
    if not allow_violations:
        if not preassign_vhg: #run the optim without CDNs
            subprocess.call(["scip", "-c", "read %s" % os.path.join(OPTIM_FOLDER,"optim.zpl"),"-c","optimize ", "-c", "write solution %s" %(os.path.join(RESULTS_FOLDER,"solutions.data")),"-c", "q"],stdout=open(os.devnull, 'wb'))
        else: #run the optim with CDN using reoptim
            subprocess.call(["scip", "-c", "read %s" % os.path.join(OPTIM_FOLDER,"optim.zpl"),"-c", "read %s" % os.path.join(RESULTS_FOLDER,"initial.sol"), "-c", "set reoptimization enable true","-c","optimize ", "-c", "write solution %s" %(os.path.join(RESULTS_FOLDER,"solutions.data")),"-c", "q"],stdout=open(os.devnull, 'wb'))

    else:
        subprocess.call(["scip", "-c", "read %s" % os.path.join(OPTIM_FOLDER,"optim.zpl"),"-c","optimize ", "-c", "write solution %s" %(os.path.join(RESULTS_FOLDER,"solutions.data")),"-c", "q"],stdout=open(os.devnull, 'wb'))
    # plotting.plotsol()
    # os.subprocess.call(["cat", "./substrate.dot", "|", "dot", "-Tpdf", "-osol.pdf"])
    with open(os.path.join(RESULTS_FOLDER,"solutions.data"), "r") as sol:
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

def solve(service, substrate,allow_violations=False,smart_ass=False,preassign_vhg=False):



    if preassign_vhg:
        service_no_cdn=copy.deepcopy(service)
        service_no_cdn.max_cdn_to_use=0
        service_no_cdn.cdn=[]
        mapping=solve(service_no_cdn, substrate,allow_violations=False,smart_ass=smart_ass,preassign_vhg=False)
        if mapping is None:
            return None
        service.vhg_hints=mapping.get_vhg_mapping()


    service.write()
    substrate.write()


    return solve_inplace(allow_violations,preassign_vhg)


