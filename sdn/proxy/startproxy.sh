DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
java -jar $DIR/proxy.jar --host=0.0.0.0 --port=8082 --debug 2>&1 &
export proxy_pid=$!
sleep 3



while true
do
	PHASE=$(cat phase.data)
	$DIR/setup-starter1.sh localhost 8888 $PHASE
	echo "we are in $PHASE "  date >> phase.log
	sleep 10
done


#echo "press enter to kill proxy"
#read
#kill -9 $proxy_pid
