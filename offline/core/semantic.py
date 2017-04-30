from offline.time.persistence import engine
import rdflib_sqlalchemy
from rdflib_sqlalchemy.store import SQLAlchemy
from rdflib.store import Store
from rdflib import Graph, Literal, Namespace, URIRef

rdflib_sqlalchemy.registerplugins()
ident = URIRef("rdflib_test")
store = SQLAlchemy(
    identifier=ident ,
    engine=engine
)

def open_triple_store():
    graph = Graph(store)
    store.engine=engine
    graph.engine=engine
    return graph

def close_triple_store(graph):
    graph.commit()
    graph.close()
