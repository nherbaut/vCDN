import os

from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from sqlalchemy.orm import sessionmaker

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')
# ENGINE_TYPE = "sqlite"
ENGINE_TYPE = "mysql"
Base = declarative_base()


# service_to_sla = Table('service_to_sla', Base.metadata,Column('service_id', Integer, ForeignKey('Service.id')),Column('sla_id', Integer, ForeignKey('Sla.id')))


class Tenant(Base):
    __tablename__ = 'tenant'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128))
    slas = relationship("Sla")


class Node(Base):
    __tablename__ = "Node"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), )
    cpu_capacity = Column(Float, )

    def __str__(self):
        return "%s\t%e" % (self.name, self.cpu_capacity)


class Edge(Base):
    __tablename__ = "Edge"
    id = Column(Integer, primary_key=True)
    node_1_id = Column(Integer, ForeignKey("Node.id"))
    node_2_id = Column(Integer, ForeignKey("Node.id"))
    delay = Column(Float, )
    bandwidth = Column(Float, )
    price_per_mbps = Column(Float, default=1)
    node_1 = relationship("Node", foreign_keys=node_1_id)
    node_2 = relationship("Node", foreign_keys=node_2_id)

    def __str__(self):
        return "%s\t%s\t%e\t%e\t%e" % (
        self.node_1.name, self.node_2.name, self.bandwidth, self.delay, self.price_per_mbps)


class ServiceNode(Base):
    __tablename__ = "ServiceNode"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(16))
    service_id = Column(Integer, ForeignKey("Service.id"))
    sla_id = Column(Integer, ForeignKey("Sla.id"))
    sla = relationship("Sla")
    cpu = Column(Float, )
    bw = Column(Float, )

    def is_vhg(self):
        return "VHG" in self.name

    def is_vcdn(self):
        return "VCDN" in self.name


class ServiceEdge(Base):
    __tablename__ = "ServiceEdge"
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("Service.id"))
    sla_id = Column(Integer, ForeignKey("Sla.id"))

    node_1_id = Column(Integer, ForeignKey("ServiceNode.id"))
    node_2_id = Column(Integer, ForeignKey("ServiceNode.id"))
    mapping_id = Column(Integer, ForeignKey("Mapping.id"))

    node_1 = relationship("ServiceNode", foreign_keys=[node_1_id], cascade="save-update")
    node_2 = relationship("ServiceNode", foreign_keys=[node_2_id], cascade="save-update")
    mapping = relationship("Mapping", cascade="save-update")
    service = relationship("Service", cascade="save-update")
    sla = relationship("Sla", cascade="save-update")

    bandwidth = Column(Float)


class NodeMapping(Base):
    __tablename__ = "NodeMapping"
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey('Node.id'))
    service_node_id = Column(Integer, ForeignKey('ServiceNode.id'))
    service_id = Column(Integer, ForeignKey('Service.id'))
    mapping_id = Column(Integer, ForeignKey('Mapping.id'))
    mapping = relationship("Mapping", cascade="save-update")
    service = relationship("Service", cascade="save-update")
    service_node = relationship('ServiceNode', cascade="save-update")
    node = relationship('Node', cascade="save-update")

    def __str__(self):
        return "%s-->%s" % (self.service_node.name, self.node.name)


class EdgeMapping(Base):
    __tablename__ = "EdgeMapping"
    id = Column(Integer, primary_key=True, autoincrement=True)
    mapping_id = Column(Integer, ForeignKey('Mapping.id'), nullable=False)

    edge_id = Column(Integer, ForeignKey('Edge.id'), nullable=False)
    edge = relationship("Edge", cascade="save-update")

    serviceEdge_id = Column(Integer, ForeignKey('ServiceEdge.id'), nullable=False)
    serviceEdge = relationship("ServiceEdge", cascade="save-update")

    def __str__(self):
        return "%s-%s ~~> %s-%s" % (
            self.serviceEdge.node_1.name, self.serviceEdge.node_2.name, self.edge.node_1.name, self.edge.node_2.name)

    @classmethod
    def backward(cls, edgeMapping):
        return cls(start_topo_node_id=edgeMapping.end_topo_node_id, end_topo_node_id=edgeMapping.start_topo_node_id,
                   start_service_node_id=edgeMapping.start_service_node_id,
                   end_service_node_id=edgeMapping.end_service_node_id)


if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

if ENGINE_TYPE is "sqlite":
    engine = create_engine('sqlite:////home/nherbaut/res.db')
else:
    engine = create_engine('mysql+mysqlconnector://root:root@127.0.0.1/paper4', )
# engine = create_engine('sqlite:///%s/res.db' % RESULTS_FOLDER)



session_factory = sessionmaker(bind=engine, autocommit=True)
Session = scoped_session(session_factory)


def drop_all():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
