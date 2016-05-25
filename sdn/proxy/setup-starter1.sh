DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


curl -X DELETE $1:$2/config/frontal
curl -X DELETE $1:$2/op/content 
curl -X PUT -d @$DIR/phase1.xml $1:$2/op/content -H "Content-type: application/xml"  -v

