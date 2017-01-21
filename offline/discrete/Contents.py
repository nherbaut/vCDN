import numpy as np


class Contents:
    def __init__(self, param=1.01):
        self.param = param

    def draw(self, count=1):
        return np.random.zipf(self.param, count)
