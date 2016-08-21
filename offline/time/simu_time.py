#!/usr/bin/env python
import os

from ..time.persistence import *
from ..time.slagen import fill_db_with_sla
import pandas as pd

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../results')

# clear the db
drop_all()

# fill the db with some data
#fill_db_with_sla()
#fill_db_with_sla()
ts, date_start, date_start_forecast,date_end_forecast = fill_db_with_sla()


for adate in pd.date_range(date_start_forecast,date_end_forecast,freq="H"):
    print findSLAByDate(adate)


