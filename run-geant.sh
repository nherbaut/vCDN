if [ "$#" -ne 1 ]; then
	./generate-geant-data.py
else
	echo "putting seed $1"
	./generate-geant-data.py --seed $1
fi

scip -b ./scpi.batch
./plotsol.py 
cat ./substrate.dot |dot -Tpdf -osol.pdf
