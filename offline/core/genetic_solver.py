import numpy as np

from offline.core.dummy_solver import DummySolver


class GeneticSolver(object):
    def __init__(self, rs):
        self.rs = rs

    def solve(self, service, substrate):
        # FINE TUNING
        pool_size = 50
        selection_size = 20
        mutation_rate = 0.3
        number_parents = 2
        min_iterations = 5
        max_identical_results = 3
        max_iterations = 10

        ####################################
        score_history = []
        mappings = []
        # initial generation
        dummy_solver = DummySolver(rs=self.rs)
        for i in range(0, pool_size):
            mapping = dummy_solver.solve(service, substrate)
            mappings.append(mapping)

        min_of_new = 0

        try:
            while len(score_history) > max_iterations or len(score_history) < min_iterations or not all(
                            score_history[-1] == item for item in score_history[-max_identical_results:]):

                # print("iteration %d / old:%lf   new:%lf" % (iteration, min_of_old, min_of_new))

                # selection "fitness proportionate selection"
                # mappings_best_breads = list(weighted_shuffle(mappings, [-2000*mapping.objective_function for mapping in mappings],                                                    selection_size, self.rs))
                mappings_best_breads = sorted(mappings, key=lambda x: x.objective_function)[0:selection_size]

                # get genotypes
                parent_genotypes = [{nm.service_node.name: nm.node.name for nm in parent.node_mappings if
                                     nm.service_node.is_vhg() or nm.service_node.is_vcdn()} for parent in
                                    mappings_best_breads]
                # cross-over
                children = []
                loci = sorted(parent_genotypes[0].keys())
                while len(children) < pool_size:
                    child = {}
                    parents = self.rs.choice(parent_genotypes, size=number_parents, replace=False)

                    cross_overs = sorted(self.rs.randint(0, len(loci), len(parents) - 1))
                    cross_over_zones = np.split(loci, cross_overs)
                    for index, cos in enumerate(cross_over_zones):
                        for locus in cos:
                            child[locus] = parents[index][locus]
                    children.append(child)

                # mutate
                for child in children:
                    for locus, gene in sorted(child.items(), key=lambda x: x[0]):
                        if self.rs.uniform() <= mutation_rate:
                            child[locus] = self.rs.choice(sorted([node.name for node in substrate.nodes]))
                        else:
                            child[locus] = gene

                children += parent_genotypes
                mappings = []
                # children computation
                for child in children:
                    dummy_solver = DummySolver(rs=self.rs, additional_node_mapping=child)
                    mapping = dummy_solver.solve(service, substrate)
                    if mapping is not None:
                        mappings.append(mapping)

                mappings = mappings + mappings_best_breads
                min_of_old = min_of_new
                min_of_new = min(mappings, key=lambda x: x.objective_function).objective_function
                score_history.append(min_of_new)
        except KeyboardInterrupt as ie:
            print("OK, interrupting genetic optimization iteration")

        mapping = sorted(mappings, key=lambda x: x.objective_function)[0]

        return mapping
