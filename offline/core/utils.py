import time
import sys

import numpy as np


class timed(object):
    '''
    decorator used to print execution time and stats on a simulation
    '''

    def __init__(self, f):
        self.f = f
        self.start = time.time()

    def __call__(self, **kwargs):
        self.start = time.time()
        res = self.f(**kwargs)
        print((        "\n%s in %lf for %d run : %lf" % (            kwargs["name"], time.time() - self.start, len(res), (time.time() - self.start) / (1 + len(res)))))
        return res




# Print iterations progress
def printProgress(iteration, total, prefix='', suffix='', decimals=1, barLength=100, file=sys.stderr):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    formatStr = "{0:." + str(decimals) + "f}"
    percents = formatStr.format(100 * (iteration / float(total)))
    filledLength = int(round(barLength * iteration / float(total)))
    bar = 'X' * filledLength + '-' * (barLength - filledLength)
    file.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    file.flush()
    if iteration == total:
        file.write('\n')
        file.flush()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def yellow(arg):
    return col(arg, bcolors.WARNING)


def red(arg):
    return col(arg, bcolors.FAIL)


def green(arg):
    return col(arg, bcolors.OKGREEN)


def col(arg, colr=bcolors.ENDC):
    return colr + str(arg) + bcolors.ENDC


def weighted_shuffle(population, population_weights, size, rs):
    return rs.choice(population, size=size, p=np.array(population_weights).astype(float) / np.sum(population_weights), replace=False)