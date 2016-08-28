import os
import pickle

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from ..time.persistence import Base

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


class Mapping(Base):
    __tablename__ = 'Mapping'
    id = Column(Integer, primary_key=True, autoincrement=True)

    service_id = Column(Integer, ForeignKey('Service.id'), nullable=False)
    service = relationship("Service", cascade="delete", back_populates="mapping")

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

    def get_objective_function(self, cpu_cost, net_cost):
        '''

        :return: the obejctive function as computed by the nodes and edges mapping
        '''
        sum_cpu = sum([1 if node_mapping.service_node.is_vhg() else 0 for node_mapping in self.node_mappings] + [
            2 if node_mapping.service_node.is_vcdn() else 0 for node_mapping in self.node_mappings]) * cpu_cost
        #sum_bw = sum([edge_mapping.serviceEdge.bandwidth for edge_mapping in self.edge_mappings if                    edge_mapping.serviceEdge.node_1.node_id != "S0"]) * net_cost
        sum_bw = sum([edge_mapping.serviceEdge.bandwidth for edge_mapping in self.edge_mappings ]) * net_cost

        return sum_cpu + sum_bw

    @classmethod
    def fromFile(cls, self, file="mapping_default.pickle"):
        with open(os.path.join(RESULTS_FOLDER, file), "r") as f:
            obj = pickle.load(self, file)
            return cls(obj.service_node_id, obj.edgesSol)
