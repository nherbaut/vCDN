#!/usr/bin/env python
import pickle
import sys

with open("results.pickle", "r") as f:
        res=pickle.load(f)


keydict={}
sys.stdout.write("Data stored:\n")
for index, key in enumerate(res.keys(),start=1):
    keydict[index]=key
    sys.stdout.write("\t- %d : %s with %d reccords\n"%(index,key,len(res[key])))



buffer=""
print "q to quit, d 1 to delete reccord 1"
buffer=sys.stdin.readline()
while buffer != "q\n":

    user_input=buffer.split()
    index=(int(user_input[1]))
    if user_input[0]=="d" and  keydict[index] in res and len(user_input)==2:
        del res[keydict[index]]
        print "reccord %s deleted" % keydict[index]
    else:
        print "error - no one here"
    buffer=sys.stdin.readline()



with open("results.pickle", "w") as f:
        pickle.dump(res,f)