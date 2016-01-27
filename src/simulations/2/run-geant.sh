if [ "$#" -ne 1 ]; then
	./generate-geant-data.py --refresh
else
#	echo "putting seed $1"
	./generate-geant-data.py --seed $1 --refresh
fi


scip -b ./scpi.batch -q &2>/dev/null
#./plotsol.py 
#cat ./substrate.dot |dot -Tpdf -osol.pdf
#echo "seed=$1"
export obf=`cat solutions.data |sed -rn "s/objective value: + ([0-9\.]+)$/\1/p"`

if [ -z $obf ]; then
	echo -1 >> res.data
else
	echo $obf >> res.data
fi

