# every X seconds, load the most used content

import simpy


def download_process(env, download_queue, download_delay, storage, content):
    # download time
    try:
        # get a download token
        request = download_queue.request()
        yield request
        try:
            yield env.timeout(download_delay)
            storage[content] = True
            # free the token
            download_queue.release(request)
        except simpy.Interrupt as interrupt:
            download_queue.release(request)
    except simpy.Interrupt as interrupt:
        download_queue.release(request)






class vCDN(object):
    def __init__(self, rs,env, location, graph, contentHistory, refresh_delay=30, download_delay=3, concurent_download=10):
        self.rs=rs
        self.env = env
        self.location = location
        self.storage = graph.node[self.location]["storage"]
        self.contentHistory = contentHistory
        self.refresh_delay = refresh_delay
        self.download_delay = download_delay
        self.action = env.process(self.run())
        self.concurent_download = concurent_download


    def run(self):
        downloads = []
        while True:
            download_queue = simpy.PreemptiveResource(self.env, capacity=self.concurent_download)
            for _, content in list(zip(range(self.storage.size()),
                                                self.contentHistory.getPopulars())):
                if content not in self.storage:
                    downloads.append(self.env.process(
                        download_process(self.env, download_queue, self.download_delay, self.storage, content)))
                else:
                    # push up in
                    self.storage[content] = True

            yield self.env.timeout(self.rs.poisson(self.refresh_delay, 1)[0])

            for download in downloads:
                if download.is_alive:
                    download.interrupt("refresh %s" % self.env.now)
            del downloads[:]
