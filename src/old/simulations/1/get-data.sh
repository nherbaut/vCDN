#!/usr/bin/env bash

export ALPHA=#1
./subgen.py --vhgcount=1 --vcdncount=1  --vhgdelayR=$ALPHA  --vcdndelayR=$ALPHA --vcdncpuR=$((200-$ALPHA)) --sourcebwR=$((200-$ALPHA))
SEED=$RANDOM
./generate-geant-data.py --seed=$SEED
export RES=$(./run-geant.sh $SEED)
while [ "$RES" -eq "1" ]; do
echo "failed with $ALPHA ($RES)"
SEED=$RANDOM;
./generate-geant-data.py --seed=$SEED
ALPHA=$(($ALPHA-1))
./subgen.py --vhgcount=1 --vcdncount=1  --vhgdelayR=$ALPHA --cdndelayR=$ALPHA --vcdndelayR=$ALPHA --vcdncpuR=$((200-$ALPHA)) --sourcebwR=$((200-$ALPHA))
RES=$(./run-geant.sh $SEED)
echo $ALPHA
done
ALPHA=$(($ALPHA-10))
./subgen.py --vhgcount=1 --vcdncount=1  --vhgdelayR=$ALPHA --cdndelayR=$ALPHA --vcdndelayR=$ALPHA --vcdncpuR=$((200-$ALPHA)) --sourcebwR=$((200-$ALPHA))

	for i in $(seq 1 10);

		do for j in $(seq 1 10);
			do 
			./subgen.py --vhgcount=$i --vcdncount=$j
			OUTPUT=$(./run-geant.sh $SEED );
			echo $i $j $OUTPUT;
			done
		done


