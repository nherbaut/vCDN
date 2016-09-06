import os
import pickle

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from ..time.persistence import Base

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')
PRICING_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../pricing')


class Mapping(Base):
    __tablename__ = 'Mapping'
    id = Column(Integer, primary_key=True, autoincrement=True)

    service_id = Column(Integer, ForeignKey('Service.id'), nullable=False)
    service = relationship("Service", cascade="save-update", back_populates="mapping")

    node_mappings = relationship("NodeMapping", cascade="all")
    edge_mappings = relationship("EdgeMapping", cascade="all")
    objective_function = Column(Float)

    def dump_cdn_node_mapping(self):
        '''

        :return: [("CDN1","1021"),("CDN2","1125")]
        '''
        return [(nm.service_node.node_id, nm.node.id) for nm in self.node_mappings if
                nm.service_node.node_id.lower().startswith("cdn")]

    def dump_starter_node_mapping(self):
        '''

        :return: [("S2","1021"),("S3","1125")]
        '''
        return [(nm.service_node.node_id, nm.node.id) for nm in self.node_mappings if
                nm.service_node.node_id.lower().startswith("s")]

    def dump_node_mapping(self):
        return [(nm.node.id,nm.service_node.node_id) for nm in self.node_mappings]

    def dump_edge_mapping(self):
        '''

        :return: [("1241","1242","VHG1","VCDN1"),("5123","5123","VHG3","VCDN3")]
        '''
        return [(em.edge.node_1, em.edge.node_2, em.serviceEdge.node_1.node_id, em.serviceEdge.node_2.node_id) for
                em in self.edge_mappings]

    def __init__(self, node_mappings=node_mappings, edge_mappings=edge_mappings, objective_function=objective_function):
        self.node_mappings = node_mappings
        self.edge_mappings = edge_mappings
        self.objective_function = objective_function

    def save(self, file="mapping", id="default"):
        with open(os.path.join(RESULTS_FOLDER, file + "_" + id), "w") as f:
            pickle.Pickler(f).dump(self)

    def get_vhg_mapping(self):
        return filter(lambda x: "VHG" in x.service_node_id, self.node_mappings)

    def get_objective_function(self):
        '''

        :return: the obejctive function as computed by the nodes and edges mapping
        '''

        with open(os.path.join(PRICING_FOLDER, "cdn", "pricing_for_one_instance.properties")) as f:
            vcdn_cpu_price = float(f.read())

        with open(os.path.join(PRICING_FOLDER, "vmg", "pricing_for_one_instance.properties")) as f:
            vhg_cpu_price = float(f.read())

        with open(os.path.join(PRICING_FOLDER, "net.cost.data")) as f:
            net_cost = float(f.read())

        sum_cpu = sum(
            [node_mapping.service_node.cpu * vhg_cpu_price if node_mapping.service_node.is_vhg() else vcdn_cpu_price for
             node_mapping
             in self.node_mappings])

        sum_bw = sum([edge_mapping.serviceEdge.bandwidth for edge_mapping in self.edge_mappings]) * net_cost

        return sum_cpu + sum_bw

    @classmethod
    def fromFile(cls, self, file="mapping_default.pickle"):
        with open(os.path.join(RESULTS_FOLDER, file), "r") as f:
            obj = pickle.load(self, file)
            return cls(obj.service_node_id, obj.edgesSol)

    def __sub__(self, b):
        '''
        TODO: implement
        :param b:
        :return:
        '''
        return 0
