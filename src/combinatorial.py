from collections import defaultdict
from itertools import chain, combinations
import sys
import numpy as np

n = 5
nodes = ["S"+str(i) for i in range(1,n+1)]
c = 3


def toto(problem):
    res = []
    if problem[1] == problem[0]:  # trivial
        return np.ones(problem[0]).tolist()
    elif problem[1] == 1:  # also trivial
        return [[problem[0]]]
    elif problem[1] == 2:  # solving the pb for 2

        for i in range(1, problem[0] / 2 + 1):
            res.append([i, problem[0] - i])
        return res
    else:
        for i in range(1, problem[0] - problem[1]):
            for j in toto([problem[0] - i, problem[1] - 1]):
                res.append([i] + j)
        return res


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


data = defaultdict(list)
for i in powerset(nodes ):
    if len(i) > 0:
        data[len(i)].append(i)

didi = [map(lambda x: int(x), x.split(" ")) for x in
        set([" ".join(map(lambda x: str(x), (sorted(x)))) for x in toto([n, c])])]


class Tree:
    def __init__(self, parent=None, node=("root",),distance=lambda x:len(x)):
        self.node = node
        self.children = []
        self.parent = parent
        self.score=None
        self.d=distance
        self.best_leaf=None

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
                my_best_children=self.score if self.score is not None else 0
                my_value=self.d(self.node)
                if self.parent.score is None or my_best_children+my_value < self.parent.score:
                    self.parent.score=my_value + my_best_children
                    self.parent.best_leaf=(self.node,self.best_leaf)










class AncesterError(Exception):
    pass


def build_exhaustive_tree(data, settings, tree=Tree()):
    '''

    :param data: {1: [("a","b","c"], 2: [("a","b")]}
    :param settings: [1,2,2]
    :param tree:
    :return:
    '''
    if len(settings)==0:
        return

    for j in data[settings[0]]:
        try:
            for k in j:
                if tree.has_ancester(k):
                    raise AncesterError()
            subtree=Tree(node=j, parent=tree)
            tree.children.append(subtree)
            build_exhaustive_tree(data,settings[1:],subtree)

        except AncesterError:
                continue


for i in didi:
    tree=Tree()
    build_exhaustive_tree(data, i,tree)
    tree.compute_best_leaf()
    print i
    print tree.score
    print tree.best_leaf
