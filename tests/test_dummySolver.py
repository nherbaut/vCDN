import unittest
from unittest import TestCase

from offline.core.dummy_solver import DummySolver
from offline.core.genetic_solver import GeneticSolver
from offline.tools.api import *


class TestServiceGraphGeneratorFactory(TestCase):
    def test_dummy(self):
        rs, su = clean_and_create_experiment()
        solver = DummySolver(rs)
        start_nodes, cdn_nodes = generate_sla_nodes(su, ["RAND(2,2)"], ["RAND(2,2)"], rs)
        sla = create_sla(start_nodes, cdn_nodes, 10000000, su=su)
        factory = ServiceGraphGeneratorFactory(sla)
        generators = factory.get_full_class_generator()
        for generator in generators:
            for topology in generator.get_service_topologies():
                service=Service(topology,sla,solver)
                service.generate_mapping()

    def test_genetic(self):
        rs, su = clean_and_create_experiment()
        solver = GeneticSolver(rs)
        start_nodes, cdn_nodes = generate_sla_nodes(su, ["RAND(2,2)"], ["RAND(2,2)"], rs)
        sla = create_sla(start_nodes, cdn_nodes, 10000000, su=su)
        factory = ServiceGraphGeneratorFactory(sla)
        generators = factory.get_full_class_generator()
        topology=next(next(generators).get_service_topologies())
        service = Service(topology, sla, solver)
        service.generate_mapping()




if __name__ == '__main__':
    unittest.main()