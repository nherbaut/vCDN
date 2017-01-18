#!/usr/bin/env python
# run simulation for paper 5
# import simpy
# from offline.core.substrate import Substrate
from offline.core.sla import generate_random_slas
from offline.core.service import Service
from offline.time.persistence import Session, Tenant
from offline.tools.ostep import clean_and_create_experiment

# create the topology and the random state
rs, su = clean_and_create_experiment(("powerlaw", (100, 1, 0.2, 1, 1000000000000, 2, 20)), 3)

# add the session and the tentant.
session = Session()
tenant = Tenant()
session.add(tenant)

slas = generate_random_slas(rs, su,
                            count=1,
                            user_count=1000000,
                            max_start_count=11,
                            max_end_count=11,
                            tenant=tenant,
                            sourcebw=0,
                            min_start_count=10,
                            min_end_count=10)

service=Service.get_optimal(slas)


