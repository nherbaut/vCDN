# every X seconds, load the most used content
import logging

from offline.core.utils import *


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
            old = list(self.storage.keys())
            for content in reversed(self.contentHistory.getPopulars(windows=200, count=100)):
                self.storage[content] = True
                yield self.env.timeout(self.download_delay)
            yield self.env.timeout(self.refresh_delay)
            new = list(self.storage.keys())
            added_items = [i for i in new if i not in old]
            removed_items = [i for i in old if i not in new]
            still_items = [i for i in new if i in old]
            #logging.debug("%s now contains %s %s %s" % (                self.location, still_items, green(str(added_items)), red(str(removed_items))))
