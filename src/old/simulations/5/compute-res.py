#!/usr/bin/env python
import fileinput
import numpy as np

data=[line for line in fileinput.input()]
success=[float(i) for i in filter(lambda x: "-1" not in x ,data)]
print "%d\t%d\t%lf\t%lf\t%lf\t%lf" % (len(data)-len(success),len(success),np.mean(success),np.min(success),np.max(success),np.std(success))
