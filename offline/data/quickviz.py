#
import os
import matplotlib.pyplot as plt
DATA_FOLDER="/home/nherbaut/workspace/algotel2016-code/offline/data/db"
for file in [file for file in os.listdir(DATA_FOLDER) if "daily" in file]:
	data=[float(line.split(",")[1]) for line in open(os.path.join(DATA_FOLDER,file)).read().split("\n") if len(line.split(","))==2]
	plt.plot(data)
	plt.title(file)
	plt.show()
