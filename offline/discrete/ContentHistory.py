import pandas as pd


class ContentHistory:
    def __init__(self):
        self.data = []

    def push(self, data):
        self.data.append(data)

    def getPopulars(self, windows=200, count=5):
        return pd.DataFrame(self.data).tail(windows)[0].value_counts().index[:count].values
