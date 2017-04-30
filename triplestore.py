import unittest

import rdflib_sqlalchemy
from rdflib import plugin, Graph, Literal, URIRef
from rdflib.store import Store
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF

rdflib_sqlalchemy.registerplugins()


class SQLASQLiteGraphTestCase(unittest.TestCase):
    ident = URIRef("rdflib_test")
    uri = Literal("mysql+mysqlconnector://root:root@127.0.0.1/paper4")
    #uri = Literal('sqlite://')  # In-memory

    def setUp(self):
        store = plugin.get("SQLAlchemy", Store)(identifier=self.ident)
        self.graph = Graph(store, identifier=self.ident)
        self.graph.open(self.uri, create=True)

    def tearDown(self):
        #self.graph.destroy(self.uri)
        try:
            self.graph.close()
        except:
            pass

    def test01(self):
        self.assert_(self.graph is not None)

        for a,b,c in self.graph:
            print("%s %s %s" % (a,b,c))
        self.graph.commit()
        print(self.graph)


if __name__ == '__main__':
    unittest.main()
