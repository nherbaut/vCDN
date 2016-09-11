#!/usr/bin/env python
# from functools import partial

from offline.tools.forecast_bench import perform_forecast_bench, plot_forecast_bench

# import offline.time.slaplot



# do_simu(migration_costs_func=lambda x: sum([abs(y[0] - y[1]) for y in x]) * 10,
#        sla_pricer=partial(price_slas, f=partial(p, r=1, m=24)))
means = perform_forecast_bench("./offline/data/")
d = "\n\t".join([x["file"] for index, x in
                 enumerate(sorted(means, key=lambda x: x["MAPE"]))if x["MAPE"] > 1])
print("%s" % d)
plot_forecast_bench(means)
# merge_with_forecast("/home/nherbaut/workspace/algotel2016-code/offline/data/New-York-IX-daily-in_5T.csvx.out","/home/nherbaut/workspace/algotel2016-code/offline/time/forecast.csv","/home/nherbaut/Desktop/out.txt")
