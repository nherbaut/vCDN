#!/usr/bin/env bash


if [ "$#" -ne 1 ]; then
        ./generate-geant-data.py --file basic.graphml --start 0 --cdn 7 --refresh
else
        ./generate-geant-data.py --seed $1 --file basic.graphml --start 0 --cdn 7 --refresh
fi

scip -b ./scpi.batch  
./plotsol.py 
cat ./substrate.dot |dot -Tpdf -osol.pdf
echo "seed=$1"
