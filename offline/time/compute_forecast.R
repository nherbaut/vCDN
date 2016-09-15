#!/usr/bin/env Rscript
#define output file for plot


library("xts")
library("forecast")
library("optparse")
library("rPython")


option_list = list(

make_option(c("-p", "--plot"), action="store_true", default=FALSE),
make_option(c("-o", "--out"), type="character", default="./dummy", help="output file name [default= %default]", metavar="character"),
make_option(c("-i", "--in_file"), default="../data/ma-i-daily_1H.csvx", type="character", help="intput file name [default= %default]", metavar="character"),
make_option(c("-l", "--lengthforecast"), type="numeric", default=24, help="Number of forcast to generate", metavar="numeric"),
make_option(c("-t", "--limit"), type="numeric", default=24, help="limit reading the file up to ith element", metavar="numeric")

);
opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);



in_file<-opt$in_file;
out<-opt$out;
limit<-opt$limit;
plot<-opt$plot;
lengthforecast<-opt$lengthforecast;


print(in_file)
print(out)
print(limit)
print(plot)
print(lengthforecast)





python.load("resample.py")
python.call("resample",in_file,paste(in_file,"out",sep="."))
v<-read.csv(file=paste(in_file,"out",sep="."),header=FALSE)


#Load time serie library
fc_len<-limit

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
fc<-forecast(m,level=c(95,80),lengthforecast)
fcmean<-as.xts(append(coredata(fc$x),fc$mean),v1)
fc95<-as.xts(append(coredata(fc$x),fc$upper[,"95%"]),v1)
fc80<-as.xts(append(coredata(fc$x),fc$upper[,"80%"]),v1)
fc0<-as.xts(v2,v1)
fc_merged<-merge(fcmean,fc95,fc80,fc0)
print(out)
write.zoo(file=out,fc_merged,sep = ",")
print(paste("csv data writter in " , out))


    if(opt$plot){
        outfile<-paste(out,".pdf",sep="")
        pdf(file=outfile)
        plot(fc)
        print(paste("pdf data writter in " , outfile))
    }

