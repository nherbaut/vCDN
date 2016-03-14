#!/usr/bin/env python


import substrate
from sla import get_sla
from solver import solve
from service import Service

rejected_threshold = 10
rejected = 0
su = substrate.get_substrate()

while rejected < rejected_threshold:
    sla = get_sla()
    service = Service.fromSla(sla)
    mapping = None
    while mapping == None:
        mapping = solve(service, su)
        if mapping == None:
            if service.relax() == False:
                rejected = rejected + 1
                break
        else:
            su.consume_service(service,mapping)
