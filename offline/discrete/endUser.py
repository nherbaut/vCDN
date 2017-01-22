class User(object):
    def __init__(self, env, ticker, content_generator):
        self.env = env
        self.action = env.process(self.run())
        self.ticker = ticker
        self.content_generator = content_generator

    def run(self):
        while True:
            yield self.env.timeout(self.ticker())
            self.consume_next_content()

    def consume_next_content(self):
        pass
