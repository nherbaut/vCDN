import os
import pickle

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from ..time.persistence import Base

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


class Mapping(Base):
    __tablename__ = 'Mapping'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sla_id = Column(Integer, ForeignKey('Sla.id'),nullable=False)
    sla = relationship("Sla", cascade="save-update")
    node_mappings = relationship("NodeMapping", cascade="save-update")
    edge_mappings = relationship("EdgeMapping", cascade="save-update")
    objective_function = Column(Float)

    '''

    bandwidth = Column(Float)
    delay = Column(Float)
    tenant_id = Column(Integer, ForeignKey('tenant.id'))
    max_cdn_to_use = Column(Integer)
    tenant = relationship("Tenant", back_populates="slas")
    start_nodes = relationship(
        "TopoNode",
        secondary=slas_to_start_nodes,
        back_populates="slas")
    end_nodes = relationship(
        "TopoNode",
        secondary=slas_to_start_nodes,
        back_populates="slas")
    '''

    def __init__(self, node_mappings=node_mappings, edge_mappings=edge_mappings, objective_function=objective_function,
                 violations=[]):
        self.node_mappings = node_mappings
        self.edge_mappings = edge_mappings
        self.objective_function = objective_function
        self.violations = violations

    def write(self):
        self.save()

    def save(self, file="mapping", id="default"):
        with open(os.path.join(RESULTS_FOLDER, file + "_" + id), "w") as f:
            pickle.Pickler(f).dump(self)

    def get_vhg_mapping(self):
        return filter(lambda x: "VHG" in x.service_node_id, self.node_mappings)

    @classmethod
    def fromFile(cls, self, file="mapping_default.pickle"):
        with open(os.path.join(RESULTS_FOLDER, file), "r") as f:
            obj = pickle.load(self, file)
            return cls(obj.service_node_id, obj.edgesSol)
