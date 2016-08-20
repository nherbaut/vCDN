#!/usr/bin/env Rscript
#define output file for plot


library("xts")
library("forecast")
library("optparse")
library("rPython")



option_list = list(
    make_option(c("-r", "--random"), action="store_true", default=TRUE),
    make_option(c("-p", "--plot"), action="store_true", default=TRUE),
    make_option(c("-o", "--out"), type="character", default="./forecast.csv", help="output file name [default= %default]", metavar="character"),
    make_option(c("-i", "--in"), type="character", default="../data/marseille.csv", help="intput file name [default= %default]", metavar="character"),
	make_option(c("-l", "--lengthforecast"), type="numeric", default=30, help="Number of forcast to generate", metavar="numeric"),
	make_option(c("-t", "--limit"), type="numeric", default=30, help="limit reading the file up to ith element", metavar="numeric")
	
); 

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

if(opt$random==TRUE){
	print("Generating random data")
	python.load("random_traffic.py")
	python.call("generate_random_traffic",output_path=opt$out,size=100)
	v<-read.csv(file=opt$out,header=FALSE)
}else {
	print("Generating random data")
	#read simulation file
	v<-read.csv(file="../data/marseille.csv",header=FALSE)
}


#Load time serie library
fc_len<-opt$limit

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
#predict
fc<-forecast(m,level=c(95,80),opt$lengthforecast)
fcmean<-as.xts(append(coredata(fc$x),fc$mean),v1)
fc95<-as.xts(append(coredata(fc$x),fc$upper[,"95%"]),v1)
fc80<-as.xts(append(coredata(fc$x),fc$upper[,"80%"]),v1)
fc0<-as.xts(v2,v1)
fc_merged<-merge(fcmean,fc95,fc80,fc0)
write.zoo(file="forecast.csv",fc_merged,sep = ",")
if(opt$plot){
outfile<-paste(opt$out,".pdf",sep="")
pdf(file=outfile)
plot(fc)
print(paste("written " , outfile))
}


