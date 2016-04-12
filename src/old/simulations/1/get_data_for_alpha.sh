#!/usr/bin/env bash

export ALPHA=$1
export SEED=$2
./subgen.py --vhgcount=1 --vcdncount=1  --vhgdelayR=$ALPHA  --vcdndelayR=$ALPHA --vcdncpuR=$ALPHA --sourcebwR=$ALPHA
./generate-geant-data.py --seed=$SEED

export RES=$(./run-geant.sh $SEED)

if [ "$RES" -ne "0" ]; then

	for i in $(seq 1 10);

		do for j in $(seq 1 10);
			do 
			./subgen.py --vhgcount=$i --vcdncount=$j
			OUTPUT=$(./run-geant.sh $SEED );
			echo $i $j $OUTPUT;
			done
		done
		exit 0
else

exit 1

fi

