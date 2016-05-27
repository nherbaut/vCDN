DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOST=localhost
PORT=8888

PHASE=`cat $DIR/proxy/phase.data`
curl -X DELETE $HOST:$PORT/config/frontal
curl -X DELETE $HOST:$PORT/op/content >> phase.log
curl -X PUT -d @$DIR/proxy/$PHASE $HOST:$PORT/op/content -H "Content-type: application/xml"  -v >> phase.log
