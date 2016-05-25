DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
java -jar $DIR/proxy.jar --host=0.0.0.0 --port=8082 --debug 2>&1 &
export proxy_pid=$!
sleep 3
$DIR/setup-starter1.sh localhost 8888
#echo "press enter to kill proxy"
#read
#kill -9 $proxy_pid
