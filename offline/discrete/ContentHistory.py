import pandas as pd


class ContentHistory:
    def __init__(self, windows=200, count=5):
        self.data = []
        self.windows = windows
        self.count = count

    def push(self, data):
        # logging.debug("pushing new value in history")
        self.data.append(data)

    def getPopulars(self):
        # logging.debug("popular now %s" % pd.DataFrame(self.data).tail(windows)[0].value_counts().index[:count])
        df = pd.DataFrame(self.data).tail(self.windows)
        if len(df) > 0:
            return df[0].value_counts().index[:self.count].values
        else:
            return []
