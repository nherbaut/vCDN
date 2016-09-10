#!/bin/bash

rm *.csvx

scp -i ~/.ssh/girafe ubuntu@demo-girafe.nextnet.top:/home/ubuntu/girafe-ixp-data-extractor/out/ECIX/*daily*csvx .
scp -i ~/.ssh/girafe ubuntu@demo-girafe.nextnet.top:/home/ubuntu/girafe-ixp-data-extractor/out/LINX/*daily*csvx .
scp -i ~/.ssh/girafe ubuntu@demo-girafe.nextnet.top:/home/ubuntu/girafe-ixp-data-extractor/out/Megaport/*daily*csvx .
scp -i ~/.ssh/girafe ubuntu@demo-girafe.nextnet.top:/home/ubuntu/girafe-ixp-data-extractor/out/NIX.CZ/*daily*csvx .


FILES=./*.csvx
for f in $FILES
do
  #../../time/resample.py -i $f  -o $f
  compute_forecast.R
  echo $f "done"
done
