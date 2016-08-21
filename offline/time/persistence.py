from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
import os

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

Base = declarative_base()


class Tenant(Base):
    __tablename__ = 'tenant'""
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    slas = relationship("SLA", back_populates="tenant")


class SLA(Base):
    __tablename__ = 'sla'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime)
    end = Column(DateTime)
    bandwidth = Column(Float)
    tenant_id = Column(Integer, ForeignKey('tenant.id'))
    tenant = relationship("Tenant", back_populates="slas")


engine = create_engine('sqlite:///%s/example.db'%RESULTS_FOLDER)
Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()



def drop_all():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)


def findSLAByDate(date):
    return session.query(SLA).filter(SLA.start <= date).filter(SLA.end > date).all()
