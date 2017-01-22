# every X seconds, load the most used content
import logging


class vCDN(object):
    def __init__(self, env, location, graph, contentHistory, refresh_delay=30, download_delay=3):
        self.env = env
        self.location = location
        self.storage = graph.node[self.location]["storage"]
        self.contentHistory = contentHistory
        self.refresh_delay = refresh_delay
        self.download_delay = download_delay
        self.action = env.process(self.run())

    def run(self):
        while True:
            yield self.env.timeout(self.refresh_delay)
            for content in self.contentHistory.getPopulars(windows=200, count=5):
                self.storage[content] = True
                yield self.env.timeout(self.download_delay)
            logging.debug("%s now contains %s" % (self.location, list(self.storage.keys())))
