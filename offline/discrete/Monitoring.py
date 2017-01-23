import collections

import pandas as pd


class Monitoring:
    data = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))

    @classmethod
    def getdf(cls):
        return pd.DataFrame.from_dict(Monitoring.data)
