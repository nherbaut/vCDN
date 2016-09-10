from functools import partial

from offline.pricing.generator import price_slas, p
from offline.time.simu_time import do_simu

# import offline.time.slaplot



do_simu(migration_costs_func=lambda x: sum([abs(y[0] - y[1]) for y in x]) * 10,
        sla_pricer=partial(price_slas, f=partial(p, r=1, m=24)))
# perform_forecast_bench("./offline/data/db")
# merge_with_forecast("/home/nherbaut/workspace/algotel2016-code/offline/data/New-York-IX-daily-in_5T.csvx.out","/home/nherbaut/workspace/algotel2016-code/offline/time/forecast.csv","/home/nherbaut/Desktop/out.txt")
