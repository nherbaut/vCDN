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
    name = Column(String(16))
    slas = relationship("Sla", back_populates="tenant")



slas_to_start_nodes = Table('slas_to_start_nodes', Base.metadata,
                            Column('startnode_id', String(16), ForeignKey('TopoNode.id')),
                            Column('sla_id', Integer, ForeignKey('Sla.id'))
                            )


class TopoNode(Base):
    __tablename__ = "TopoNode"
    id = Column(String(16), primary_key=True)




class NodeMapping(Base):
    __tablename__ = "NodeMapping"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topo_node_id = Column(String(16), ForeignKey('TopoNode.id'))
    service_node_id = Column(String(16))
    mapping_id = Column(Integer, ForeignKey('Mapping.id'))


class EdgeMapping(Base):
    __tablename__ = "EdgeMapping"
    id = Column(Integer, primary_key=True, autoincrement=True)
    mapping_id = Column(Integer, ForeignKey('Mapping.id'),nullable=False)
    start_topo_node_id = Column(String(16), ForeignKey('TopoNode.id'))
    end_topo_node_id = Column(String(16), ForeignKey('TopoNode.id'))
    start_service_node_id = Column(String(16))
    end_service_node_id = Column(String(16))

    @classmethod
    def backward(cls,edgeMapping):
        return cls(start_topo_node_id=edgeMapping.end_topo_node_id, end_topo_node_id=edgeMapping.start_topo_node_id, start_service_node_id=edgeMapping.start_service_node_id, end_service_node_id=edgeMapping.end_service_node_id)



#engine = create_engine('sqlite:///%s/example.db' % RESULTS_FOLDER, echo=True)
engine = create_engine('mysql+mysqldb://root:root@localhost/paper4',echo=True)

session = sessionmaker(bind=engine)()


def drop_all():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
