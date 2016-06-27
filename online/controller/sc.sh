rm output.txt
ryu-manager ./StatGrabber.py --log-file output.txt 2>/dev/null 1>/dev/null &
kst2count=$(ps -ef |grep kst2|wc -l)

if [ $kst2count == 1 ]; then
	kst2 ./finalplot.kst&
fi

echo "monitoring output.txt"




header='time,id,port,rx_packets,rx_byes,rx_errors,tx_packets,tx_bytes,tx_errors,rx_packetsps,rx_byesps,rx_errorsps,tx_packetsps,tx_bytesps,tx_errorsps\n'
when-changed ./output.txt -c "echo $header > 32.txt; cat output.txt |grep ' *32, *2,' >> 32.txt ; echo $header > 31.txt; cat output.txt |grep ' *31, *2,' >> 31.txt ;"



killall ryu-manager
