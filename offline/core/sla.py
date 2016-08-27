import scipy
import scipy.integrate as integrate
from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from ..time.persistence import session, Base, service_to_sla

tcp_win = 65535.0


def concurrentUsers(t, m, sigma, duration):
    return integrate.quad(
        lambda x: 1 / (sigma * scipy.sqrt(2 * scipy.pi) * scipy.exp(-(x - m) ** 2.0 / (2 * sigma ** 2))), t - duration,
        t)[0]


class SlaNodeSpec(Base):
    __tablename__ = 'SlaNodeSpec'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sla_id = Column(Integer, ForeignKey("Sla.id"), nullable=False)
    sla = relationship("Sla", cascade="all")
    toponode_id = Column(String(16), ForeignKey("Node.id"), nullable=False)
    topoNode = relationship("Node", order_by="Node.id",cascade="all")
    type = Column(String(16))


class Sla(Base):
    __tablename__ = 'Sla'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    bandwidth = Column(Float)
    delay = Column(Float)
    max_cdn_to_use = Column(Integer)


    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=False)
    tenant = relationship("Tenant", cascade="save-update")


    sla_node_specs = relationship("SlaNodeSpec", cascade="save-update")

    services = relationship("Service", secondary=service_to_sla, back_populates="slas")

    substrate_id = Column(Integer, ForeignKey("Substrate.id"), nullable=False)
    substrate = relationship("Substrate")

    def __str__(self):
        return "%d %d %lf %lf" % (self.start, self.cdn, self.delay, self.bandwidth)

    def __init__(self, *args, **kwargs):
        self.start_date = kwargs.get("start_date", None)
        self.end_date = kwargs.get("end_date", None)
        self.bandwidth = kwargs.get("bandwidth", None)
        self.tenant_id = kwargs.get("tenant_id", None)
        self.max_cdn_to_use = kwargs.get("max_cdn_to_use", None)
        self.delay = kwargs.get("delay", None)
        for start_node in kwargs.get("start_nodes", []):
            self.sla_node_specs.append(SlaNodeSpec(toponode_id=start_node.id, type="start"))
        for cdn_node in kwargs.get("cdn_nodes", []):
            self.sla_node_specs.append(SlaNodeSpec(toponode_id=cdn_node.id, type="cdn"))
        self.substrate = kwargs.get("substrate", None)

    def get_start_nodes(self):
        return filter(lambda x: x.type == "start", self.sla_node_specs)

    def get_cdn_nodes(self):
        return filter(lambda x: x.type == "cdn", self.sla_node_specs)


def findSLAByDate(date):
    return session.query(Sla).filter(Sla.start_date <= date).filter(Sla.end_date > date).all()


def write_sla(sla, seed=None):
    with open("CDN.nodes.data", 'w') as f:
        f.write("%s \n" % sla.cdn)

    with open("starters.nodes.data", 'w') as f:
        f.write("%s \n" % sla.start)


def generate_random_slas(rs, substrate, count=1000, start_count=0, end_count=0, tenant=None):
    res = []
    for i in range(0, count):
        bitrate = getRandomBitrate(rs)
        # bitrate = rs.choice([   400000, 500000, 600000])
        concurent_users = max(rs.normal(20000, 5000), 1000)
        # concurent_users = max(rs.normal(20000, 5000), 5000)
        time_span = max(rs.normal(24 * 60 * 60, 60 * 60), 0)
        movie_duration = max(rs.normal(60 * 60, 10 * 60), 0)

        delay = tcp_win / bitrate * 1000.0
        bandwidth = count * bitrate * movie_duration / time_span


        if not (start_count>0 and end_count>0):
            start_count=rs.randint(low=1, high=5)
            end_count= rs.randint(low=1, high=start_count)

        random_nodes= rs.choice(substrate.nodes, size=start_count+end_count, replace=False)


        start_nodes = random_nodes[:start_count]

        cdn_nodes = random_nodes[start_count:]



        res.append(
            Sla(start_date=None, end_date=None,
                bandwidth=bandwidth ,
                tenant_id=tenant.id,
                start_nodes=start_nodes ,
                cdn_nodes=cdn_nodes,
                substrate=substrate,
                delay=delay
                ))

    return res


def getRandomBitrate(rs):
    n = rs.uniform(0, 100)
    if n < 25:  # LD
        return 666666
    elif n < 75:
        return 1555555  # SD
    else:
        return 5000000  # HD
