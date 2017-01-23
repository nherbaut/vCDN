import logging

import pandas as pd


class ContentHistory:
    def __init__(self):
        self.data = []

    def push(self, data):
        #logging.debug("pushing new value in history")
        self.data.append(data)

    def getPopulars(self, windows=200, count=5):
        # logging.debug("popular now %s" % pd.DataFrame(self.data).tail(windows)[0].value_counts().index[:count])
        df = pd.DataFrame(self.data).tail(windows)
        if len(df) > 0:
            return df[0].value_counts().index[:count].values
        else:
            return []
