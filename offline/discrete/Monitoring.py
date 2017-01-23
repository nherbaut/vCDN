import collections

import pandas as pd
import numpy as np

class Monitoring:
    data_sum = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    data_avg = collections.defaultdict(lambda: collections.defaultdict(lambda: []))

    @classmethod
    def getdf(cls):
        data = cls.data_sum.copy()
        data.update({key:{k: np.mean(v) for k, v in value.items()}for key, value in cls.data_avg.items()})
        return pd.DataFrame.from_dict(data)

    @classmethod
    def push(cls, column, index, data):
        cls.data_sum[column][index] = cls.data_sum[column][index] + data

    @classmethod
    def push_average(cls, column, index, data):
        cls.data_avg[column][index].append(data)
