./generate-geant-data.py --file basic.graphml --start 0 --cdn 7
scip -b ./scpi.batch
./plotsol.py 
cat ./substrate.dot |dot -Tpdf -osol.pdf
