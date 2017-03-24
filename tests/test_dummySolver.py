from unittest import TestCase

from offline.core.ilpsolver import DummySolver
from offline.tools.api import *


class TestServiceGraphGeneratorFactory(TestCase):
    def test_full(self):
        rs, su = clean_and_create_experiment()
        solver = DummySolver(rs)
        start_nodes, cdn_nodes = generate_sla_nodes(su, ["RAND(4,4)"], ["RAND(10,10)"], rs)
        sla = create_sla(start_nodes, cdn_nodes, 10000000, su=su)
        factory = ServiceGraphGeneratorFactory(sla)
        generators = factory.get_full_class_generator()
        for generator in generators:
            for topology in generator.get_service_topologies():
                service=Service(topology,sla,solver)
                service.solve()

