java -jar proxy.jar --host=0.0.0.0 --port=8082 --debug &
export proxy_pid=$!
sleep 3
./setup-starter1.sh localhost 8888
echo "press enter to kill proxy"
read
kill -9 $proxy_pid
