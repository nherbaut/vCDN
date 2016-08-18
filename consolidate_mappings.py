from offline.db.persistance import DAO
from offline.core.solver import *
from offline.core.service import Service, ServiceSpec
from offline.core.substrate import Substrate
from offline.tools.step import do_step
import numpy.random
rs=numpy.random.RandomState()
#su0 = Substrate.fromGraph(rs, "offline/data/Geant2012.graphml")
su0=Substrate.fromSpec(5,5,10**10,1,100)
su0.write()
d=DAO()
d.cleanup()

for i in range (0,10):
    do_step(False,False,True,False,(5,5),2,1,1,1)


res=d.findall()

for i in range(1,len(res)+1):
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








