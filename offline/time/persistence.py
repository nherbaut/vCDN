import os

from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Table

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

Base = declarative_base()

service_to_sla = Table('service_to_sla', Base.metadata,
                       Column('service_id', Integer, ForeignKey('Service.id')),
                       Column('sla_id', Integer, ForeignKey('Sla.id'))
                       )


class Tenant(Base):
    __tablename__ = 'tenant'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(16))
    slas = relationship("Sla")


class Node(Base):
    __tablename__ = "Node"
    id = Column(String(16), primary_key=True)
    cpu_capacity = Column(Float, )

    def __str__(self):
        return "%s\t%e" % (self.id, self.cpu_capacity)




class Edge(Base):
    __tablename__ = "Edge"
    id = Column(Integer, primary_key=True)
    node_1 = Column(String(16), ForeignKey("Node.id"))
    node_2 = Column(String(16), ForeignKey("Node.id"))
    delay = Column(Float, )
    bandwidth = Column(Float, )

    def __str__(self):
        return "%s\t%s\t%e\t%e" % (self.node_1, self.node_2, self.bandwidth, self.delay)


class ServiceNode(Base):
    __tablename__ = "ServiceNode"
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(16))
    service_id = Column(Integer, ForeignKey("Service.id"))
    sla_id = Column(Integer, ForeignKey("Sla.id"))
    cpu = Column(Float, )
    def is_vhg(self):
        return "VHG" in self.node_id


    def is_vcdn(self):
        return "VCDN" in self.node_id

class ServiceEdge(Base):
    __tablename__ = "ServiceEdge"
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey("Service.id"))
    sla_id = Column(Integer, ForeignKey("Sla.id"))

    node_1_id = Column(Integer, ForeignKey("ServiceNode.id"))
    node_2_id = Column(Integer, ForeignKey("ServiceNode.id"))

    node_1 = relationship("ServiceNode", foreign_keys=[node_1_id], cascade="all")
    node_2 = relationship("ServiceNode", foreign_keys=[node_2_id], cascade="all")

    bandwidth = Column(Float)


class NodeMapping(Base):
    __tablename__ = "NodeMapping"
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(16), ForeignKey('Node.id'))
    sla_id = Column(Integer, ForeignKey('Sla.id'))
    service_node_id = Column(Integer, ForeignKey('ServiceNode.id'))
    service_id = Column(Integer, ForeignKey('Service.id'))
    mapping_id = Column(Integer, ForeignKey('Mapping.id'))

    mapping = relationship("Mapping")
    service = relationship("Service")
    sla = relationship("Sla")
    service_node = relationship('ServiceNode')
    node = relationship('Node')


class EdgeMapping(Base):
    __tablename__ = "EdgeMapping"
    id = Column(Integer, primary_key=True, autoincrement=True)
    mapping_id = Column(Integer, ForeignKey('Mapping.id'), nullable=False)

    edge_id = Column(Integer, ForeignKey('Edge.id'), nullable=False)
    edge = relationship("Edge", cascade="save-update")

    serviceEdge_id = Column(Integer, ForeignKey('ServiceEdge.id'), nullable=False)
    serviceEdge = relationship("ServiceEdge", cascade="save-update")

    @classmethod
    def backward(cls, edgeMapping):
        return cls(start_topo_node_id=edgeMapping.end_topo_node_id, end_topo_node_id=edgeMapping.start_topo_node_id,
                   start_service_node_id=edgeMapping.start_service_node_id,
                   end_service_node_id=edgeMapping.end_service_node_id)


# engine = create_engine('sqlite:///%s/example.db' % RESULTS_FOLDER, echo=True)
engine = create_engine('mysql+mysqldb://root:root@127.0.0.1/paper4', )

session = sessionmaker(bind=engine)()


def drop_all():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
