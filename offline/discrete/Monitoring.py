import collections

import pandas as pd


class Monitoring:
    data = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))

    @classmethod
    def getdf(cls):
        return pd.DataFrame.from_dict(Monitoring.data)

    @classmethod
    def push(cls, column, index, data):
        cls.data[column][index] = cls.data[column][index] + data
