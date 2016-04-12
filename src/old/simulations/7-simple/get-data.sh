rm res.data; for i in `seq 1 1000`; do ./run-geant.sh $RANDOM; done; cat res.data |./compute-res.py
