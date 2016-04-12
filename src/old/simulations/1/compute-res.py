#!/usr/bin/env python
import fileinput
import numpy as np

data=[line for line in fileinput.input()]
success=[float(i) for i in filter(lambda x: "-1" not in x ,data)]
print "%lf\t" % (100.0*(len(data)-len(success))/len(data))
