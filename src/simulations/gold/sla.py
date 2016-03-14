import scipy
import scipy.integrate as integrate

tcp_win = 65535


def concurrentUsers(t, m, sigma, duration):
    return integrate.quad(
        lambda x: 1 / (sigma * scipy.sqrt(2 * scipy.pi) * scipy.exp(-(x - m) ** 2.0 / (2 * sigma ** 2))), t - duration,
        t)[0]


class Sla:
    def __init__(self, bitrate, count, time_span, movie_duration, start, cdn):
        self.start = start
        self.cdn = cdn
        self.delay = tcp_win / bitrate
        self.bandwidth = count * bitrate

        # Throughput = TCPWindow / round-trip-delay


def get_sla():
    return Sla(500000, 100, 4 * 60 * 60, 1 * 60 * 60, 16, 20)


def write_sla(sla, seed=None):
    with open("CDN.nodes.data", 'w') as f:
        f.write("%s \n" % sla.cdn)

    with open("starters.nodes.data", 'w') as f:
        f.write("%s \n" % sla.start)
