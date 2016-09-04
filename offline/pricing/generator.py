import csv
from functools import partial


def get_calculator(file_path="azure_cdn_pricing_zone1.properties"):
    '''

    :param file_path: specs for cdn pricing
    :return: return a function used to compute cdn price according to porperties file
    '''
    threshold_prices = {}
    with open(file_path, "r") as f:
        for key, value in csv.reader(filter(lambda row: row[0] != '#', f), delimiter=","):
            threshold_prices[key] = value

    return partial(calculator, threshold_prices=threshold_prices)


def calculator(quantity_gb, threshold_prices):
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
