import numpy as np
import pickle
from collections import defaultdict
import matplotlib.pyplot as plt


means=pickle.load(open("means.pickle"))
def filterIX(x):
	ixs={"IX":"IX1","linx":"IX2","ecix":"IX3"}
	for k in list(ixs.keys()):
		if k in x:
			return ixs[k]	
	else:
	  return "IX4"



data_means=defaultdict(lambda: [])
data_std=defaultdict(lambda: [])

for item in ["sla_vio_mean","sla_vio_fc80", "sla_vio_fc95",]:
	vio_means=[(filterIX(x["file"]),x[item]) for x in means ]
	vio_means+=[("zall",x[item]) for x in means ]
	res=defaultdict(lambda: [])
	for x in vio_means:
		res[x[0]].append(x[1])
	print(("%s"%item))
	for k in sorted(res.keys()):
	  data_means[k].append(np.mean(res[k]))
	  data_std[k].append(np.sqrt(np.std(res[k])))
	  print(("%s\t%lf\t(%lf)"%(k,np.mean(res[k]),np.sqrt(np.std(res[k])))))
	
	  
	  
fig, ax = plt.subplots()



ind = np.arange(5)
width = 0.25
ax.set_xticks(ind + width)
ax.set_xticklabels(('IX1', 'IX2', 'IX3', 'IX4', 'All'))
ax.set_ylim((0,100))
ax.set_ylabel('Average % of SLA Violation')
#ax.set_title('Scores by group and gender')
ax.set_xticks(ind + width)


rects1 = ax.bar(ind, [data_means[x][0] for x in sorted(data_means)], width, color='r', yerr=[data_std[x][0] for x in sorted(data_std)])
rects2 = ax.bar(ind+width, [data_means[x][1] for x in sorted(data_means)], width, color='g', yerr=[data_std[x][1] for x in sorted(data_std)])
rects3 = ax.bar(ind+2*width, [data_means[x][2] for x in sorted(data_means)], width, color='b', yerr=[data_std[x][2] for x in sorted(data_std)])



from matplotlib.font_manager import FontProperties

fontP = FontProperties()
fontP.set_size('small')

ax.legend((rects1[0], rects2[0], rects3[0]), ("Mean Forecasts","80% CI", "95% CI", ),loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3, fancybox=True, shadow=True)



def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%d' % int(height),
                ha='center', va='bottom')
                
autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

plt.grid()
plt.savefig("sla_vio.svg")
plt.show(block=True)

fig.gca()





data_means=defaultdict(lambda: [])
data_std=defaultdict(lambda: [])

for item in ["price_fcmean","price_fc80", "price_fc95",]:
	vio_means=[(filterIX(x["file"]),x[item]) for x in means ]
	vio_means+=[("zall",x[item]) for x in means ]
	res=defaultdict(lambda: [])
	for x in vio_means:
		res[x[0]].append(x[1])
	print(("%s"%item))
	for k in sorted(res.keys()):
	  data_means[k].append(np.mean(res[k]))
	  data_std[k].append(np.sqrt(np.std(res[k])))
	  print(("%s\t%lf\t(%lf)"%(k,np.mean(res[k]),np.sqrt(np.std(res[k])))))
	
	  
	  
fig, ax = plt.subplots()



ind = np.arange(5)
width = 0.25
ax.set_xticks(ind + width)
ax.set_xticklabels(('IX1', 'IX2', 'IX3', 'IX4', 'All'))
#ax.set_ylim((0,100))
ax.set_ylabel('Average price increase wrt mean forecast price')

ax.set_xticks(ind + width)




rects1 = ax.bar(ind, [100*data_means[x][0]/data_means[x][0] for x in sorted(data_means)], width, color='r', )
rects2 = ax.bar(ind+width, [100*data_means[x][1]/data_means[x][0] for x in sorted(data_means)], width, color='g', )
rects3 = ax.bar(ind+2*width, [100*data_means[x][2]//data_means[x][0] for x in sorted(data_means)], width, color='b', )



from matplotlib.font_manager import FontProperties

fontP = FontProperties()
fontP.set_size('small')

ax.legend((rects1[0], rects2[0], rects3[0]), ("Mean Forecasts","80% CI", "95% CI", ),loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3, fancybox=True, shadow=True)



def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%d' % int(height),
                ha='center', va='bottom')
                
autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

plt.grid()
plt.savefig("prices_vio.svg")
plt.show(block=True)


data_means=defaultdict(lambda: [])
data_std=defaultdict(lambda: [])

for item in ["MAPE","MASE",]:
	vio_means=[(filterIX(x["file"]),x[item]) for x in means ]
	vio_means+=[("zall",x[item]) for x in means ]
	res=defaultdict(lambda: [])
	for x in vio_means:
		res[x[0]].append(x[1])
	print(("%s"%item))
	for k in sorted(res.keys()):
	  data_means[k].append(np.mean(res[k]))
	  data_std[k].append(np.sqrt(np.std(res[k])))
	  print(("%s\t%lf\t(%lf)"%(k,np.mean(res[k]),np.sqrt(np.std(res[k])))))
	
	  
	  
fig, ax = plt.subplots()



ind = np.arange(5)
width = 0.25
ax.set_xticks(ind + width)
ax.set_xticklabels(('IX1', 'IX2', 'IX3', 'IX4', 'All'))
ax.set_ylim((0,6))
ax.set_ylabel('Metric Value')
#ax.set_title('Scores by group and gender')
ax.set_xticks(ind + width)


rects1 = ax.bar(ind, [data_means[x][0] for x in sorted(data_means)], width, color='r', yerr=[data_std[x][0] for x in sorted(data_std)])
rects2 = ax.bar(ind+width, [data_means[x][1] for x in sorted(data_means)], width, color='g', yerr=[data_std[x][1] for x in sorted(data_std)])




from matplotlib.font_manager import FontProperties

fontP = FontProperties()
fontP.set_size('small')

ax.legend((rects1[0], rects2[0]), ("MAPE","MASE" ),loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=2, fancybox=True, shadow=True)



def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%1.1lf' % height,
                ha='center', va='bottom')
                
autolabel(rects1)
autolabel(rects2)

plt.grid()
plt.savefig("mapemase.svg")
plt.show(block=True)







