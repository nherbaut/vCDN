import os
import pickle

import networkx as nx
from networkx.readwrite import json_graph
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy import and_
from sqlalchemy.orm import relationship, aliased

from ..time.persistence import Base, Session, Edge, Node

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')
PRICING_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../pricing')


class Mapping(Base):
    __tablename__ = 'Mapping'
    id = Column(Integer, primary_key=True, autoincrement=True)

    service_id = Column(Integer, ForeignKey('Service.id'), nullable=True)
    substrate_id = Column(Integer, ForeignKey('Substrate.id'))
    service = relationship("Service", cascade="save-update", back_populates="mapping")

    node_mappings = relationship("NodeMapping", cascade="all")
    edge_mappings = relationship("EdgeMapping", cascade="all")
    substrate = relationship("Substrate", cascade="none")

    objective_function = Column(Float)

    def __str__(self):
        print("NODES")
        for nm in self.node_mappings:
            print(nm)

        print("EDGES")
        for em in self.edge_mappings:
            print(em)

    def to_json(self):
        session = Session()
        g = nx.Graph()
        for nm in self.node_mappings:
            g.add_node(nm.service_node.name, mapping=nm.node.name, cpu=nm.service_node.cpu,
                       bandwidth=nm.service_node.bw)
        for em in self.edge_mappings:
            if not g.has_edge(em.serviceEdge.node_1.name, em.serviceEdge.node_2.name):
                g.add_edge(em.serviceEdge.node_1.name, em.serviceEdge.node_2.name, mapping=[],
                           bandwith=em.serviceEdge.bandwidth)

            g[em.serviceEdge.node_1.name][em.serviceEdge.node_2.name]["mapping"].append(
                (em.edge.node_1.name, em.edge.node_2.name))

        # aggregate delay on the substrate to have the real delay
        for service_start, service_end, data in g.edges(data=True):
            delay = 0
            for start, end in data["mapping"]:
                Node1 = aliased(Node)
                Node2 = aliased(Node)

                delay += session.query(Edge).join((Node1, Node1.name == start)).join(
                    (Node2, Node2.name == end)).filter(
                    and_(Edge.node_1_id == Node1.id, Edge.node_2_id == Node2.id)).one().delay
            g[service_start][service_end]["delay"] = delay

        return json_graph.node_link_data(g)

    def dump_cdn_node_mapping(self):
        '''

        :return: [("CDN1","1021"),("CDN2","1125")]
        '''
        return [(nm.service_node.name, nm.node.name) for nm in self.node_mappings if
                nm.service_node.name.lower().startswith("cdn")]

    def dump_starter_node_mapping(self):
        '''

        :return: [("S2","1021"),("S3","1125")]
        '''
        return [(nm.service_node.name, nm.node.name) for nm in self.node_mappings if
                nm.service_node.name.lower().startswith("s")]

    def dump_node_mapping(self):
        return [(nm.node.name, nm.service_node.name) for nm in self.node_mappings]

    def dump_edge_mapping(self):
        '''

        :return: [("1241","1242","VHG1","VCDN1"),("5123","5123","VHG3","VCDN3")]
        '''
        return [(em.edge.node_1.name, em.edge.node_2.name, em.serviceEdge.node_1.name, em.serviceEdge.node_2.name) for
                em in self.edge_mappings]

    def __init__(self, node_mappings=node_mappings, edge_mappings=edge_mappings, objective_function=objective_function):

        self.node_mappings = node_mappings
        self.edge_mappings = edge_mappings
        self.objective_function = objective_function

    def save(self, file="mapping", id="default"):
        with open(os.path.join(RESULTS_FOLDER, file + "_" + id), "w") as f:
            pickle.Pickler(f).dump(self)

    def get_vhg_mapping(self):
        return [x for x in self.node_mappings if "VHG" in x.service_node_id]

    def update_objective_function(self):
        self.objective_function = self.get_objective_function()

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

    @classmethod
    def get_migration_cost(cls, a, b, migration_costs_func):
        res = {}
        res = {nm.service_node.id: (nm.service_node.cpu, 0) for nm in a.node_mappings}
        for nm in b.node_mappings:
            if nm.service_node.service_id in res:
                res[nm.service_node.id] = (res[nm.service_node.service_id][0], nm.service_node.cpu)
            else:
                res[nm.service_node.id] = (0, nm.service_node.cpu)

        return migration_costs_func([x for x in list(res.values()) if x[0] + x[1] != 0])
