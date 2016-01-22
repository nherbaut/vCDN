./generate-geant-data.py 
scip -b ./scpi.batch
./plotsol.py 
cat ./substrate.dot |dot -Tpdf -osol.pdf
