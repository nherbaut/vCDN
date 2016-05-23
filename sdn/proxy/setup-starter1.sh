echo curl -X DELETE $1:$2/config/frontal
curl -X DELETE $1:$2/config/frontal


curl -X DELETE $1:$2/op/content 
echo curl -X DELETE $1:$2/op/content

echo curl -X PUT -d @phase1.xml $1:$2/op/content -H "Content-type: application/xml"  -v
curl -X PUT -d @phase1.xml $1:$2/op/content -H "Content-type: application/xml"  -v

