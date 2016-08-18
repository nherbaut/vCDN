#define output file for plot
#pdf(file="output.pdf")

#Load time serie library
library("xts")
library("forecast")
fc_len<-30

#generate test data or use real trace from IXP
#create a new experiment 
system("python main2.py > simu.csv")
v<-read.csv(file="simu.csv",header=FALSE)
#read simulation file
#v<-read.csv(file="test2.csv",header=FALSE)
#create variables from the data
#unpack list to vector
v2<-unlist(v["V2"])
v1<-unlist(v["V1"])
#convert vector from string to date
v1<-as.POSIXct(v1)
#create the time serie object we fit
data<-ts(v2[1:(length(v1)-fc_len)],frequency=24)
#automatically fit sarima
m<-auto.arima(data)
print(m)
#save plot to pdf file
fc<-forecast(m,level=c(95,80),fc_len)
#display predictions
fc<-forecast(m,level=c(95,80),fc_len)
fcmean<-as.xts(append(coredata(fc$x),fc$mean),v1)
fc95<-as.xts(append(coredata(fc$x),fc$upper[,"95%"]),v1)
fc80<-as.xts(append(coredata(fc$x),fc$upper[,"80%"]),v1)
fc0<-as.xts(v2,v1)
fc_merged<-merge(fcmean,fc95,fc80,fc0)
write.zoo(file="forecast.csv",fc_merged,sep = ",")
#plot(fc)


