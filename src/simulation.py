from service import Service
import numpy as np
import substrate
import utils
from solver import solve

from src.sla import generate_random_slas


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
    rs = np.random.RandomState(seed=seed)
    result = []
    cost_function = []
    rejected = 0
    su = substrate.get_substrate(rs)
    slas = generate_random_slas(rs, su, sla_count)

    while rejected < rejected_threshold:
        best_objective_function = None
        best_mapping = None
        count_transformation_loop = 0
        sla = slas.pop()
        service = Service.fromSla(sla)
        mapping = None
        while mapping is None:
            mapping = solve(service, su)
            if best_objective_function is not None:
                print
                "proactive relaxation: %lf\t%lf" % (best_objective_function, mapping.objective_function)
            if mapping is None:
                if not service.relax(relax_vhg, relax_vcdn):
                    rejected += 1
                    break
                count_transformation_loop += 1

            elif is_cost_function_pathologic(cost_function, mapping.objective_function, proactive):
                if not service.relax(relax_vhg, relax_vcdn):
                    rejected += 1
                    break
                best_objective_function = max(best_objective_function, mapping.objective_function)
                best_mapping = mapping
                mapping = None
                continue


            else:

                cost_function.append(mapping.objective_function)
                count_transformation += count_transformation_loop
                mapping.save()
                su.consume_service(service, mapping)
                su.write()
                result.append("%s\t%d\t%d" % (su, sla_count - len(slas) - rejected, count_transformation))

    return result
