import csv
from functools import partial


def get_vmg_calculator(sys_spec_file_path="vmg/vio_vmg_pricing_aws.properties",
                       net_spec_file_path="vmg/bandwidth_per_user.properties"):
    '''
    :param sys_spec_file_path: specs for vmg pricing
    :return: a function used to compute vmh price accordint to prop file
    '''

    sys_specs = None
    with open(sys_spec_file_path, "r") as f:
        for key, value in csv.reader(filter(lambda row: row[0] != '#', f), delimiter=","):
            sys_specs = (float(key), float(value))
    with open(net_spec_file_path, "r") as f:
        net_specs = float(list(csv.reader(filter(lambda row: row[0] != '#', f)))[0][0])

    return partial(vmg_calculator, sys_spec=sys_specs, net_spec=net_specs)


def get_vcdn_calculator(file_path="cdn/azure_cdn_pricing_zone1.properties"):
    '''

    :param file_path: specs for cdn pricing
    :return: return a function used to compute cdn price according to porperties file
    '''
    threshold_prices = {}
    with open(file_path, "r") as f:
        for key, value in csv.reader(filter(lambda row: row[0] != '#', f), delimiter=","):
            threshold_prices[key] = value

    return partial(vcdn_calculator, threshold_prices=threshold_prices)


def vmg_calculator(bandwidth_gbps, sys_spec, net_spec):
    return bandwidth_gbps * 10 ** 9 / net_spec / sys_spec[0] * sys_spec[1]


def vcdn_calculator(quantity_gb, threshold_prices):
    '''

    :param quantity_gb: the quantity of bytes to get the the pricing from
    :param threshold_prices: specs for pricing
    :return: a price in USD
    '''
    res = 0
    for threshold, price in threshold_prices.items():
        if (quantity_gb >= threshold):
            res += 10 * 0.087
            quantity_gb -= threshold
        else:
            res += quantity_gb * 0.087
            break
    return res
