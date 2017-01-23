#!/usr/bin/env python3
import matplotlib.pyplot as plt
import pandas as pd


e=pd.DataFrame.from_csv("eval.csv")
e=pd.DataFrame(index=[pd.Timedelta(seconds=i)+pd.Timestamp('2012-05-01 00:00:00') for i in e.index],data=e.values,columns=list(e))
e1M=e.resample("60s").sum().fillna(0)

price=pd.DataFrame.from_csv("eval.csv")
price=pd.DataFrame(index=[pd.Timedelta(seconds=i)+pd.Timestamp('2012-05-01 00:00:00') for i in price.index],data=price["price"].values,columns=["price"])
price=price.resample("60s").bfill().fillna(0)

#e1M["USER"].cumsum().plot()

plt.plot(e1M.index,e1M["REQUEST"],)
plt.plot(e1M.index,e1M["HIT.HIT"],)
plt.plot(e1M.index,e1M["HIT.CDN"],)
plt.plot(e1M.index,e1M["HIT.VCDN"],)

plt.legend(["REQUESTS","HIT.HIT","HIT.CDN","HIT.VCDN"], loc='upper left')


plt.show()


plt.plot(price.index,price["price"],)
plt.show()

