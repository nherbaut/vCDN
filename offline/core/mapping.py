import os
import pickle

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from ..time.persistence import Base, service_to_sla

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


class Mapping(Base):
    __tablename__ = 'Mapping'
    id = Column(Integer, primary_key=True, autoincrement=True)

    service_id = Column(Integer, ForeignKey('Service.id'), nullable=False)
    service = relationship("Service", cascade="save-update",back_populates="mapping")

    node_mappings = relationship("NodeMapping", cascade="all")
    edge_mappings = relationship("EdgeMapping", cascade="all")
    objective_function = Column(Float)


    def __init__(self, node_mappings=node_mappings, edge_mappings=edge_mappings, objective_function=objective_function):
        self.node_mappings = node_mappings
        self.edge_mappings = edge_mappings
        self.objective_function = objective_function


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
