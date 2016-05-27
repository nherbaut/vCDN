DIR=`dirname $(readlink -f $0)`
HOST=localhost
PORT=8888

PHASE=`cat $DIR/phase.data`
echo "##1" $DIR >> phase.log
echo "##2" $PHASE >> phase.log
curl -X DELETE $HOST:$PORT/config/frontal
curl -X DELETE $HOST:$PORT/op/content >> phase.log
echo curl -X PUT -d @$DIR/phase$PHASE.xml $HOST:$PORT/op/content -H "Content-type: application/xml"  -v >> phase.log
curl -X PUT -d @$DIR/phase$PHASE.xml $HOST:$PORT/op/content -H "Content-type: application/xml"  -v >> phase.log
