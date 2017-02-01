import collections
import logging

import numpy as np
import pandas as pd

from offline.core.utils import green


class Monitoring:
    data_sum = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
    data_avg = collections.defaultdict(lambda: collections.defaultdict(lambda: []))

    @classmethod
    def getdf(cls):
        data = cls.data_sum.copy()
        data.update({key: {k: np.mean(v) for k, v in value.items()} for key, value in cls.data_avg.items()})
        return pd.DataFrame.from_dict(data)

    @classmethod
    def push(cls, column, index, data, opt=""):
        logging.debug("[%s][%s][%s]=%s" % (column, "%.2f" % index, green(opt), data))
        cls.data_sum[column]["%.2f" % index] +=  data

    @classmethod
    def push_average(cls, column, index, data):
        cls.data_avg[column]["%.2f" % index].append(data)
