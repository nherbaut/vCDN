START=`date +%s`
DIR=`dirname $(readlink -f $0)`


echo -e "time,phase" > $DIR/phase_data.log
echo -e "1" > $DIR/phase.data
while true; do

WHAT=`$DIR/31bw.py --file_path=$DIR/../controller/31.txt --phase_data_file=$DIR/phase.data`
PHASE=`cat $DIR/phase.data`

if [[ "$WHAT" == "2" ]] ; then
	echo "changing phase from 1 to 2"
	echo "2" > $DIR/phase.data
elif [[ "$WHAT" == "1" ]] ; then
echo "changing phase from 2 to 1"
	echo "1" > $DIR/phase.data
fi

echo -e "import time\nprint \"%s,%d\"%(time.time()-"$START","$PHASE")"| python >> $DIR/phase_data.log
sleep 1

done;
