import unittest
from functools import partial
from unittest import TestCase

import matplotlib.pyplot as plt
import networkx as nx

from offline.core.reduced_service_graph_generator import ComposedServiceGraphGenerator
from offline.tools.api import *


class TestFullSGFenerator(TestCase):
    def test_dummy(self):
        rs, su = clean_and_create_experiment()
        start_nodes, cdn_nodes = generate_sla_nodes(su, ["RAND(3,3)"], ["RAND(2,2)"], rs)
        sla = create_sla(start_nodes, cdn_nodes, 10000000, su=su)
        # sgg= FullServiceGraphGenerator(sla, 2, 2)

        klass = partial(HeuristicServiceGraphGenerator, solver=ILPSolver)
        #klass = partial(FullServiceGraphGenerator, disable_isomorph_check=False)
        sgg = ComposedServiceGraphGenerator(sla, klass)
        for index, sgt in enumerate(sgg.get_service_topologies()):

            nx.draw(sgt.nx_service_graph, with_labels=True,node_size=2000)
            plt.draw()
            plt.show()


if __name__ == '__main__':
    unittest.main()
