from __future__ import print_function
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.tsa as tsa
import pandas as pd
from scipy.stats import norm
import numpy as np
from patsy import dmatrices

size=200
x = np.linspace(1,size,size)
index=pd.date_range('01/01/2016', periods=size,freq="1H")
rs=np.random.RandomState()
g = pd.Series( 0,index=index)


#gaussian mixture
for i in rs.choice(x,size=size/3, replace=False):
    spread=rs.uniform(1,100)
    multiplicator=5*spread
    g+=pd.Series(norm.pdf(x,i,spread)*multiplicator, index=index)


#gaussian 24h seasonality
seasonx=x = np.linspace(1,24,24)
season_index=pd.date_range('01/01/2016', periods=24,freq="1H")
season = pd.Series( 0,index=season_index)
for i in rs.choice(x[6:-6],size=4, replace=True):
    spread=rs.uniform(1,20)
    multiplicator=g.mean()
    s=pd.Series(norm.pdf(seasonx,i,spread)*multiplicator, index=season_index)
    season+=s

for i in range (0,len(g)/len(season)):
    g=g.add(season.shift(24*i,freq="1H")*3,fill_value=0)



g=g.add(pd.Series( 0,index=index).cumsum())
for k in sorted(g.keys())[:-50]:
    print("%s,%s" % (k,g[k]))

#g.plot()
#plt.show()






