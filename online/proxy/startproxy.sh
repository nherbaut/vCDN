DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
java -jar $DIR/proxy.jar --host=0.0.0.0 --port=8082 --debug 2>&1 &
export proxy_pid=$!
sleep 3

echo "1" > $DIR/phase.data
$DIR/setup-starter1.sh |tee > proxy.log
UPDATE_CMD="$DIR/setup-starter1.sh"
echo "########################" $UPDATE_CMD
when-changed $DIR/phase.data -c "$UPDATE_CMD"
kill -9 $proxy_pid
