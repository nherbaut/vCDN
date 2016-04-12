#!/usr/bin/env python

from mapping import Mapping
from service import Service
from sla import generate_random_slas
import numpy as np
from solver import solve
from substrate import Substrate

rs = np.random.RandomState()
su=Substrate.fromFile()
sla = generate_random_slas(rs, su, 1)[0]
service = Service.fromSla(sla)
mapping = solve(service, su)
if not mapping  is None:
    su.consume_service(service,mapping)
    service.write()
    su.write()
    mapping.save()
    exit(0)
else:
    exit(1)


