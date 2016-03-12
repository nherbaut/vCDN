scip -b ./scpi.batch -q &2>/dev/null
#scip -b ./scpi.batch 
./plotsol.py 
cat ./substrate.dot |dot -Tpdf -osol.pdf
export obf=`cat solutions.data |sed -rn "s/objective value: + ([0-9\.]+)$/\1/p"`

if [ -z $obf ]; then
	echo -1 
else
	echo 1
fi

