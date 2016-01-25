if [ "$#" -ne 1 ]; then
        ./generate-geant-data.py --file basic.graphml --start 0 --cdn 7 
else
        echo "putting seed $1"
        ./generate-geant-data.py --seed $1 --file basic.graphml --start 0 --cdn 7 
fi

scip -b ./scpi.batch
./plotsol.py 
cat ./substrate.dot |dot -Tpdf -osol.pdf
echo "seed=$1"
