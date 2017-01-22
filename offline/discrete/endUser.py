import logging


class User(object):
    def __init__(self, env, location, start_time, content_drawer, content_duration=120):
        self.env = env
        self.location = location
        self.action = env.process(self.run())
        self.start_time = start_time
        self.content_drawer = content_drawer
        self.content_duration = content_duration

    def run(self):
        yield self.env.timeout(self.start_time)
        content = self.content_drawer()
        self.consume_content(content)
        yield self.env.timeout(self.content_duration)
        self.release_content(content)

    def consume_content(self, content):
        logging.debug("[%s]\t%s \t consume content %s" % (self.env.now, self.location, str(content)))

    def release_content(self, content):
        logging.debug("[%s]\t%s \t released content %s" % (self.env.now, self.location, str(content)))
