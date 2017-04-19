import unittest

import networkx as nx

from algorun import *


def equal_nodes(n1, n2):
    print("for %s and %s" % (n1["name"], n2["name"]))
    if 'B' in n1["name"] and 'B' in n2["name"]:
        print("%s %s can be the same" % (n1["name"], n2["name"]))
        return False
    else:
        print("%s %s not the same" % (n1["name"], n2["name"]))
        return True


class AlgoTest(unittest.TestCase):


    def test_all_iso(self):
        print("%d",len(list(get_all_isobase(6,6))))



    def test_trivial_then_eye(self):
        m, n = 3, 4
        row, col = 0, 0
        # initialize base matrix to all nan
        base = np.ones((m, n)) * np.nan
        # initialize remaining ones and lines
        rem_1 = n
        rem_r = m
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = pad_lines_with_zeros(base, row, col, rem_1, rem_r)
        is_triv, trivial_solver = is_trivial(base, row, col, rem_1, rem_r)
        self.assertTrue(is_triv)
        trivial_solver()
        self.assertTrue(is_finished(base, row, col, rem_1, rem_r))
        oracle = np.matrix([[1, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        self.assertTrue(np.all(oracle == base))

    def test_trivial_then_ones(self):
        m, n = 3, 4
        row, col = 0, 0
        # initialize base matrix to all nan
        base = np.ones((m, n)) * np.nan
        # initialize remaining ones and lines
        rem_1 = n
        rem_r = m
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = pad_lines_with_zeros(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = pad_lines_with_zeros(base, row, col, rem_1, rem_r)
        is_triv, trivial_solver = is_trivial(base, row, col, rem_1, rem_r)
        self.assertTrue(is_triv)
        trivial_solver()

        self.assertTrue(is_finished(base, row, col, rem_1, rem_r))
        oracle = np.matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 1]])

        # self.assertTrue(np.all(oracle==base))

    def test_all_trivial(self):
        tri = next(get_isobase(1, 1))
        self.assertEqual(tri[0][0], 1)

    def get_graph_from_matrix(self, m):
        row_count, col_count = m.shape
        g = nx.DiGraph()
        # print(m)
        # print("********gives*******")
        for i in range(0, row_count):
            for j in range(0, col_count):
                if m[i, j] == 1:
                    g.add_edge("A%d" % j, "B%d" % i)

        # print(g.edges())
        # raw_input()
        for n in g.nodes():
            g.node[n]["name"] = n
        return g

    def test_all(self):
        m, n = 3, 4
        base = get_isobase(m, n)
        self.assertEqual(len(list(base)), 6)

    '''
    def test_not_iso(self):
        i_max = 5
        j_max = 5
        for i in range(1, i_max + 1):
            for j in range(1, min(j_max + 1, i)):
                print("*******%d %d********" % (i, j))
                graphs = []
                for m in get_isobase(j, i):
                    candidate = self.get_graph_from_matrix(m)
                    for g in graphs:
                        # self.assertFalse(nx.is_isomorphic(candidate, g, equal_nodes))
                        if not nx.is_isomorphic(candidate, g, equal_nodes):
                            print(g.edges())
                            print(candidate.edges())
                            raw_input()
                    graphs.append(candidate)
    '''
    def test_split(self):
        m, n = 3, 4
        row, col = 0, 0
        # initialize base matrix to all nan
        base = np.ones((m, n)) * np.nan
        # initialize remaining ones and lines
        rem_1 = n
        rem_r = m
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)

        alt0, alt1 = split01(base, row, col, rem_1, rem_r)
        base, row, col, rem_1, rem_r = alt0

        self.assertEqual(base[0, 1], 0)
        self.assertEqual(row, 0)
        self.assertEqual(col, 2)
        self.assertEqual(rem_1, n - 1)
        self.assertEqual(rem_r, m)

        base, row, col, rem_1, rem_r = alt1
        self.assertEqual(base[0, 1], 1)
        self.assertEqual(row, 0)
        self.assertEqual(col, 2)
        self.assertEqual(rem_1, n - 2)
        self.assertEqual(rem_r, m)

    def test_finished(self):
        m, n = 3, 4
        row, col = 0, 0
        # initialize base matrix to all nan
        base = np.ones((m, n)) * np.nan
        # initialize remaining ones and lines
        rem_1 = n
        rem_r = m
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = pad_lines_with_zeros(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = pad_lines_with_zeros(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        self.assertTrue(is_finished(base, row, col, rem_1, rem_r))

    def test_trivial(self):
        m, n = 3, 4
        row, col = 0, 0
        # initialize base matrix to all nan
        base = np.ones((m, n)) * np.nan
        # initialize remaining ones and lines
        rem_1 = n
        rem_r = m
        is_triv, _ = is_trivial(base, row, col, rem_1, rem_r)
        self.assertTrue(not is_triv)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        is_triv, _ = is_trivial(base, row, col, rem_1, rem_r)
        self.assertTrue(not is_triv)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        is_triv, _ = is_trivial(base, row, col, rem_1, rem_r)
        self.assertTrue(is_triv)

    def test_fill_col(self):
        m, n = 3, 4
        row, col = 0, 0
        # initialize base matrix to all nan
        base = np.ones((m, n)) * np.nan
        # initialize remaining ones and lines
        rem_1 = n
        rem_r = m
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)

        self.assertEqual(col, 1)
        self.assertEqual(row, 0)
        self.assertEqual(rem_1, n - 1)
        self.assertEqual(rem_r, m)

        self.assertEqual(base[0, 0], 1)
        self.assertTrue(np.all(base[1:, 0] == 0))

        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)

        self.assertEqual(col, 2)
        self.assertEqual(row, 0)
        self.assertEqual(base[0, 1], 1)
        self.assertTrue(np.all(base[col:, 0] == 0))
        self.assertEqual(rem_1, n - 2)
        self.assertEqual(rem_r, m)

    def test_pad_zeros(self):
        n, m = 8, 10
        row, col = 0, 0
        # initialize base matrix to all nan
        base = np.ones((n, m)) * np.nan
        # initialize remaining ones and lines
        rem_1 = n
        rem_r = m
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = pad_lines_with_zeros(base, row, col, rem_1, rem_r)
        self.assertEqual(row, 1)
        self.assertEqual(col, 1)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        row, col, rem_1, rem_r = insert_one(base, row, col, rem_1, rem_r)
        self.assertEqual((row, col), (1, 3))
        self.assertEqual(np.sum(base[row, :col]), 2)


if __name__ == '__main__':
    #unittest.main()
    print("%d", len(list(get_all_isobase(9, 9))))
