from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Table
import os

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

Base = declarative_base()



class Tenant(Base):
    __tablename__ = 'tenant'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    slas = relationship("Sla", back_populates="tenant")
    start_pp= Column(String)
    cdn_pp = Column(String)

association_table = Table('slas_to_start_nodes', Base.metadata,
    Column('start_node_id', Integer, ForeignKey('StartNode.id')),
    Column('sla_id', Integer, ForeignKey('Sla.id'))
)


class StartNode(Base):
    __tablename__= "StartNode"
    id = Column(Integer, primary_key=True)
    slas = relationship(
        "Sla",
        secondary=association_table,
        back_populates="start_nodes")







engine = create_engine('sqlite:///%s/example.db'%RESULTS_FOLDER)
Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()



def drop_all():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)


