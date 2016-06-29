from offline.db.persistance import DAO
from offline.core.solver import *
from offline.core.service import Service, ServiceSpec
from offline.core.substrate import Substrate
import numpy.random
rs=numpy.random.RandomState()
su0 = Substrate.fromGraph(rs, "offline/data/Geant2012.graphml")
su0.write()
d=DAO()
res=d.findall()

for i in range(1,len(res)):
    Service.cleanup()
    su=su0
    su0.write()
    for index, value in enumerate(res[0:i]):

        service=value[2]
        mapping=value[3]
        service.id=str(index)
        service.write(append=True)

    m=solve_inplace()
    if m is not None:
        spec=ServiceSpec.fromFiles()
        su.consume_service(spec,m)
        print "%d %s"% (i, su)
    else:
        print "failed"








