import scipy
import scipy.integrate as integrate

tcp_win = 65535.0


def concurrentUsers(t, m, sigma, duration):
    return integrate.quad(
        lambda x: 1 / (sigma * scipy.sqrt(2 * scipy.pi) * scipy.exp(-(x - m) ** 2.0 / (2 * sigma ** 2))), t - duration,
        t)[0]


class Sla:
    def __init__(self, bitrate, count, time_span, movie_duration, start, cdn):
        self.start = start
        self.cdn = cdn
        self.delay = tcp_win / bitrate * 1000.0
        self.bandwidth = count * bitrate * movie_duration / time_span

    def __str__(self):
        return "%d %d %lf %lf" % (self.start, self.cdn, self.delay, self.bandwidth)

        # Throughput = TCPWindow / round-trip-delay


def write_sla(sla, seed=None):
    with open("CDN.nodes.data", 'w') as f:
        f.write("%s \n" % sla.cdn)

    with open("starters.nodes.data", 'w') as f:
        f.write("%s \n" % sla.start)


def generate_random_slas(rs, substrate, count=1000):
    res = []
    for i in range(0, count):
        bitrate = rs.choice([500000, 750000,  1000000, 1500000, 2000000])
        concurent_users = max(rs.normal(5000, 5000), 0) + 10
        time_span = max(rs.normal(24 * 60 * 60, 60 * 60), 0)
        movie_duration = max(rs.normal(60 * 60, 10 * 60), 0)

        start = rs.choice(substrate.nodesdict.keys())
        cdn = rs.choice(substrate.nodesdict.keys())
        res.append(Sla(bitrate, concurent_users, time_span, movie_duration, start, cdn))

    return res
