import scipy
import scipy.integrate as integrate
from bisect import bisect_right

import numpy as np
from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, String, PickleType
from sqlalchemy.orm import relationship

from ..time.persistence import Node
from ..time.persistence import Session, Base, service_to_sla

tcp_win = 65535.0


# http://nicky.vanforeest.com/probability/weightedRandomShuffling/weighted.html
def weighted_shuffle(a, w, rs):
    r = np.empty_like(a)
    cumWeights = np.cumsum(w)
    for i in range(len(a)):
        rnd = rs.uniform() * cumWeights[-1]
        j = bisect_right(cumWeights, rnd)
        r[i] = a[j]
        cumWeights[j:] -= w[j]
    return r


def concurrentUsers(t, m, sigma, duration):
    return integrate.quad(
        lambda x: 1 / (sigma * scipy.sqrt(2 * scipy.pi) * scipy.exp(-(x - m) ** 2.0 / (2 * sigma ** 2))), t - duration,
        t)[0]


class SlaNodeSpec(Base):
    __tablename__ = 'SlaNodeSpec'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sla_id = Column(Integer, ForeignKey("Sla.id"))
    sla = relationship("Sla", cascade="save-update")
    toponode_id = Column(Integer, ForeignKey("Node.id"), nullable=False)
    topoNode = relationship("Node", order_by="Node.id", cascade="save-update")
    attributes = Column(PickleType)
    type = Column(String(16))


class Sla(Base):
    __tablename__ = 'Sla'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    delay = Column(Float)
    max_cdn_to_use = Column(Integer)

    tenant_id = Column(Integer, ForeignKey('tenant.id'))
    tenant = relationship("Tenant", cascade="all")

    sla_node_specs = relationship("SlaNodeSpec", cascade="all, delete-orphan")
    services = relationship("Service", secondary=service_to_sla, back_populates="slas", cascade="save-update")

    substrate_id = Column(Integer, ForeignKey("Substrate.id"))
    substrate = relationship("Substrate", cascade="save-update")

    def __init__(self, *args, **kwargs):
        '''
        :param start_nodes: a list of nodes with their metadata includeing bandwidth {"S1":{"bandwidth":12},"S2":{"bandwidth":13}}
        :param args:
        :param kwargs:
        '''
        self.start_date = kwargs.get("start_date", None)
        self.end_date = kwargs.get("end_date", None)
        self.tenant_id = kwargs.get("tenant_id", None)
        self.max_cdn_to_use = kwargs.get("max_cdn_to_use", None)
        self.delay = kwargs.get("delay", None)
        self.substrate = kwargs.get("substrate", None)
        self.sla_node_specs = kwargs.get("sla_node_specs", [])

    def get_total_bandwidth(self):
        return sum([start_node.attributes["bandwidth"] for start_node in self.get_start_nodes()])

    def get_start_nodes(self):
        return sorted(filter(lambda x: x.type == "start", self.sla_node_specs), key=lambda x: x.toponode_id)

    def get_cdn_nodes(self):
        return sorted(filter(lambda x: x.type == "cdn", self.sla_node_specs), key=lambda x: x.toponode_id)


def findSLAByDate(date):
    session = Session()
    return session.query(Sla).filter(Sla.start_date <= date).filter(Sla.end_date > date).all()


def write_sla(sla, seed=None):
    with open("CDN.nodes.data", 'w') as f:
        f.write("%s \n" % sla.cdn)

    with open("starters.nodes.data", 'w') as f:
        f.write("%s \n" % sla.start)


def generate_random_slas(rs, substrate, count=1000, user_count=1000, max_start_count=1, max_end_count=1, tenant=None,
                         sourcebw=0, min_start_count=1,
                         min_end_count=1):
    session = Session()
    res = []
    for i in range(0, count):
        if sourcebw == 0:
            bitrate = getRandomBitrate(rs)
            # bitrate = rs.choice([   400000, 500000, 600000])
            concurent_users = max(rs.normal(20000, 5000), 1000)
            # concurent_users = max(rs.normal(20000, 5000), 5000)
            time_span = max(rs.normal(24 * 60 * 60, 60 * 60), 0)
            movie_duration = max(rs.normal(60 * 60, 10 * 60), 0)

            delay = tcp_win / bitrate * 1000.0
            bandwidth = user_count * bitrate * movie_duration / time_span
        else:
            bandwidth = sourcebw

            # get the nodes and their total bw
        nodes_by_degree = substrate.get_nodes_by_degree()
        nodes_by_bw = substrate.get_nodes_by_bw()

        cdn_nodes = weighted_shuffle(list(nodes_by_degree.keys()), np.array(list(nodes_by_degree.values())) * 100, rs)[
                    :rs.randint(min_end_count, max_end_count + 1)]
        start_nodes = weighted_shuffle(list(nodes_by_bw.keys()), list(nodes_by_bw.values()), rs)[
                      -rs.randint(min_start_count, max_start_count + 1):]
        nodespecs = []
        for sn in start_nodes:
            sn = session.query(Node).filter(Node.name == sn).one()
            nodespecs.append(
                SlaNodeSpec(type="start", topoNode=sn, attributes={"bandwidth": bandwidth / (1.0 * len(start_nodes))}))

        for sn in cdn_nodes:
            sn = session.query(Node).filter(Node.name == sn).one()
            nodespecs.append(
                SlaNodeSpec(type="cdn", topoNode=sn, attributes={"bandwidth": 0}))

        sla = Sla(start_date=None, end_date=None,
                  bandwidth=bandwidth,
                  tenant_id=tenant.id,
                  sla_node_specs=nodespecs,
                  substrate=substrate,
                  delay=delay
                  )
        session.add(sla)
        session.flush()
        res.append(sla)

    return res


def getRandomBitrate(rs):
    n = rs.uniform(0, 100)
    if n < 25:  # LD
        return 666666
    elif n < 75:
        return 1555555  # SD
    else:
        return 5000000  # HD
