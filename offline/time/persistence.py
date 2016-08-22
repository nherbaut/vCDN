import os

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Table

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

Base = declarative_base()


class Tenant(Base):
    __tablename__ = 'tenant'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    slas = relationship("Sla", back_populates="tenant")
    start_pp = Column(String)
    cdn_pp = Column(String)


slas_to_start_nodes = Table('slas_to_start_nodes', Base.metadata,
                            Column('startnode_id', Integer, ForeignKey('TopoNode.id')),
                            Column('sla_id', Integer, ForeignKey('Sla.id'))
                            )



class TopoNode(Base):
    __tablename__ = "TopoNode"
    id = Column(String, primary_key=True)
    slas = relationship("Sla", secondary=slas_to_start_nodes,cascade="save-update")


class ServiceNode(Base):
    __tablename__ = "ServiceNode"
    id = Column(String, primary_key=True)


class NodeMapping(Base):
    __tablename__ = "NodeMapping"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topo_node_id = Column(String, ForeignKey('TopoNode.id'))
    service_node_id = Column(String, ForeignKey('ServiceNode.id'))
    mapping_id = Column(Integer, ForeignKey('Mapping.id'))



class EdgeMapping(Base):
    __tablename__ = "EdgeMapping"
    id = Column(Integer, primary_key=True)
    mapping_id = Column(Integer, ForeignKey('Mapping.id'))
    start_topo_node_id = Column(String, ForeignKey('TopoNode.id'))
    end_topo_node_id = Column(String, ForeignKey('TopoNode.id'))
    start_service_node_id = Column(String, ForeignKey('ServiceNode.id'))
    end_service_node_id = Column(String, ForeignKey('ServiceNode.id'))


engine = create_engine('sqlite:///%s/example.db' % RESULTS_FOLDER, echo=True)
# engine = create_engine('mysql+mysqldb://root:root@localhost/paper4',echo=True)

session = sessionmaker(bind=engine)()


def drop_all():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
