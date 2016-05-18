import time


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
        print(        "\n%s in %lf for %d run : %lf" % (            kwargs["name"], time.time() - self.start, len(res), (time.time() - self.start) / (1 + len(res))))
        return res
