import numpy as np
import substrate
import utils
from service import Service
from sla import generate_random_slas
from solver import solve
from substrate import Substrate
from copy import deepcopy
def is_cost_function_pathologic(cost_function, objective_function, proactive):
    '''

    :param cost_function: an array that contains previous cost function values
    :param objective_function: the value of this cost function
    :param proactive: tell if the function actually does something
    :return: true if the objective_function value is considered pathologic
    '''
    if proactive:
        sample_size = 10
        if len(cost_function) < sample_size:
            return False
        cost_function_sample = cost_function[-sample_size:]
        deviation = np.mean(cost_function_sample) - objective_function
        std = np.std(cost_function_sample)
        if deviation / std > 2:
            return True
        else:
            return False
    else:
        return False


@utils.timed
def do_simu(relax_vhg, relax_vcdn, proactive, seed, sla_count, rejected_threshold):
    '''
    performs the simulation with the specified characteristics
    :param relax_vhg: True if we let the algothim increase the number of vhg
    :param relax_vcdn:  True if we let the algothim increase the number of vcdn
    :param proactive: True if we want to used the the proactive service transformation feature
    :return: an array of value corresponding to each run of the simulation with the format: substrate\t number of success, number of transforamtion done.
    '''
    count_transformation = 0

    result = []
    cost_function = []
    rejected = 0
    rs = np.random.RandomState(seed=seed)
    su = substrate.get_substrate(rs)
    su=Substrate.fromSpec(4,4,5*10**9,3,300)
    slas = sorted(generate_random_slas(rs, su, sla_count), key=lambda x: x.bandwidth)
    #slas = generate_random_slas(rs, su, sla_count)



    while rejected < rejected_threshold:
        best_objective_function = None
        best_mapping = None
        count_transformation_loop = 0
        sla = slas.pop()
        service = Service.fromSla(sla)

        mapping = None
        mapping_res=[]

        #run this algo until relaxation is over
        while True:
            print "solving for vhg=%d vcdn=%d start=%d"%(service.vhgcount,service.vcdncount,len(service.start))
            mapping = solve(service, su)
            if mapping is not None:
                mapping_res.append((deepcopy(service),deepcopy(mapping)))

            if service.relax(relax_vhg, relax_vcdn):
                service.write()
            else:
                break

        if len(mapping_res) == 0:
            rejected +=1
            continue
        else:
            mapping_res=sorted(mapping_res, key=lambda x: x[1].objective_function)
            service=mapping_res[0][0]
            mapping=mapping_res[0][1]
            #mapping.save()
            print "winner has %d\t%d" % (service.vhgcount,service.vcdncount)
            su.consume_service(service, mapping)
            su.write()

            accepted_slas=sla_count - len(slas) - rejected
            result.append("%s\t%d\t%d\t%lf" % (su, accepted_slas, len(mapping_res),float(accepted_slas)/(accepted_slas+rejected)))

    return result
