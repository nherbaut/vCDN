rm res.data; for i in `seq 1 100`; do ./run-simple.sh $RANDOM; done; cat res.data |./compute-res.py
