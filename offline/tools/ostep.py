#!/usr/bin/env python

import os

from numpy.random import RandomState

from ..core.service import Service
from ..core.sla import Sla, SlaNodeSpec
from ..core.substrate import Substrate
from ..time.persistence import Session, Base, engine, drop_all, Tenant, Node

GEANT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/Geant2012.graphml')
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')


def create_experiment_and_optimize(starts, cdns, sourcebw, topo, seed):
    session = Session()
    Base.metadata.create_all(engine)
    drop_all()

    rs = RandomState(seed)

    su = Substrate.fromSpec(topo, rs)
    su.write(RESULTS_FOLDER)
    session.add(su)
    session.flush()

    tenant = Tenant()
    session.add(tenant)

    sla_node_specs = []
    for start in starts:
        ns = SlaNodeSpec(topoNode=session.query(Node).filter(Node.name == start).one(), type="start",
                         attributes={"bandwidth": 1})
        sla_node_specs.append(ns)

    for cdn in cdns:
        ns = SlaNodeSpec(toponode_id=session.query(Node).filter(Node.name == start).one(), type="cdn",
                         attributes={"bandwidth": 1})
        sla_node_specs.append(ns)

    sla = Sla(substrate=su, delay=200, max_cdn_to_use=1, tenant_id=tenant.id, sla_node_specs=sla_node_specs)
    session.add(sla)
    session.flush()

    service = Service([sla.id])
    print("success : %lf" % service.mapping.objective_function)
