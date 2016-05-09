import sys
from collections import defaultdict
from itertools import chain, combinations, product

from solver import shortest_path


def generate_problem_combinaisons(problem):
    res = []
    if problem[1] == problem[0]:  # trivial
        return [[1 for x in range(1, problem[0] + 1)], ]
    elif problem[1] == 1:  # also trivial
        return [[problem[0]]]
    elif problem[1] == 2:  # solving the pb for 2

        for i in range(1, problem[0] / 2 + 1):
            res.append([i, problem[0] - i])
        return res
    else:
        for i in range(1, problem[0] - problem[1] + 1):
            for j in generate_problem_combinaisons([problem[0] - i, problem[1] - 1]):
                res.append([i] + j)
        return res


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


class Tree:
    def __init__(self, parent=None, node=("root",), distance=lambda x: len(x)):
        self.node = node
        self.children = []
        self.parent = parent
        self.score = None
        self.d = distance
        self.best_leaf = None

    def has_ancester(self, node):
        if self.parent is not None:

            if node in self.node:
                return True
            else:
                return self.parent.has_ancester(node)

        return False

    def compute_best_leaf(self):

        for c in self.children:
            c.compute_best_leaf()

        if self.parent is not None:
            my_best_children = self.score if self.score is not None else 0
            my_value = self.d(self.node)
            if self.parent.score is None or my_best_children + my_value < self.parent.score:
                self.parent.score = my_value + my_best_children
                self.parent.best_leaf = [self.node, ]
                if self.best_leaf is not None:
                    for i in self.best_leaf:
                        self.parent.best_leaf.append(i)


class AncesterError(Exception):
    pass


cache = {}


def do_dist(bunch):
    if bunch in cache:
        return cache[bunch]
    else:
        asum = 0
        for i in filter(lambda x: x[0] != x[1],
                        map(lambda x: x.split(" "), set([" ".join(sorted(i)) for i in product(bunch, bunch)]))):


            value = shortest_path_cached(str(i[0]), str(i[1]))

            if value is not None:
                asum += value
            else:
                print
                "failure: %s" % str(i)

        return asum


def build_exhaustive_tree(data, settings, tree):
    '''

    :param data: {1: [("a","b","c"], 2: [("a","b")]}
    :param settings: [1,2,2]
    :param tree:
    :return:
    '''
    if len(settings) == 0:
        return

    for j in data[settings[0]]:
        try:
            for k in j:
                if tree.has_ancester(k):
                    raise AncesterError()
            subtree = Tree(node=j, parent=tree, distance=tree.d)
            tree.children.append(subtree)
            build_exhaustive_tree(data, settings[1:], subtree)

        except AncesterError:
            continue




def shortest_path_cached(node1,node2):
    if (node1,node2) not in cache:
        cache[(node1,node2)]=shortest_path(node1,node2)

    return cache[(node1,node2)]


def get_vhg_cdn_mapping(vhgs,cdns):
    '''

    :param vhgs: [ ("1025",'vhg1'), ("1026",'vhg2')]
    :param cdns: [ ("1025",'cdn1'), ("1026",'cdn3')]
    :return: [ "vhg1":"cdn3"]
    '''
    res={}
    for vhg in vhgs:
        best=sys.maxint
        for cdn in cdns:
            value=shortest_path_cached(vhg[0],cdn[0])
            if value < best:
                best==value
                res[vhg[1]]=cdn[1]
    return res


def clusterStart(nodes, class_count):
    data = defaultdict(list)
    for i in powerset(nodes):
        if len(i) > 0:
            data[len(i)].append(i)

    combinaisons = [map(lambda x: int(x), x.split(" ")) for x in
                    set([" ".join(map(lambda x: str(x), (sorted(x)))) for x in
                         generate_problem_combinaisons([len(nodes), class_count])])]

    min_score = sys.maxint
    candidate = None

    for i in combinaisons:
        tree = Tree(distance=do_dist)
        build_exhaustive_tree(data, i, tree)
        tree.compute_best_leaf()
        if tree.score < min_score:
            min_score = tree.score
            candidate = tree.best_leaf


    i=1
    res={}
    for x in candidate:
        for y in x:
          res[y]=i
        i+=1

    return res
