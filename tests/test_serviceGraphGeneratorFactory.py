from unittest import TestCase

from offline.core.ilpsolver import ILPSolver
from offline.tools.api import *


class TestServiceGraphGeneratorFactory(TestCase):
    def test_full(self):
        rs, su = clean_and_create_experiment()
        start_nodes, cdn_nodes = generate_sla_nodes(su, ["RAND(4,4)"], ["RAND(2,2)"], rs)
        sla = create_sla(start_nodes, cdn_nodes, 10000000, su=su, rs=rs)
        factory = ServiceGraphGeneratorFactory(sla)
        generators = factory.get_full_class_generator()
        self.assertEqual(sum([len(generator.getTopos()) for generator in generators]), 32714)

    def test_full_filtered(self):
        rs, su = clean_and_create_experiment()
        start_nodes, cdn_nodes = generate_sla_nodes(su, ["RAND(3,3)"], ["RAND(2,2)"], rs)
        sla = create_sla(start_nodes, cdn_nodes, 10000000, su=su, rs=rs)
        factory = ServiceGraphGeneratorFactory(sla)
        generators = factory.get_full_class_generator_filtered()
        self.assertEqual(sum([len(generator.getTopos()) for generator in generators]), 66)

    def test_reduced(self):
        rs, su = clean_and_create_experiment()
        start_nodes, cdn_nodes = generate_sla_nodes(su, ["RAND(4,4)"], ["RAND(2,2)"], rs)
        sla = create_sla(start_nodes, cdn_nodes, 10000000, su=su, rs=rs)
        factory = ServiceGraphGeneratorFactory(sla)
        generators = factory.get_reduced_class_generator(ILPSolver())
        self.assertEqual(sum([len(generator.getTopos()) for generator in generators]), 10)
