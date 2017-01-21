#!/usr/bin/env python
import pickle
import sys


import readline
import cmd



with open("results.pickle", "r") as f:
        res=pickle.load(f)


keydict={}
sys.stdout.write("Data stored:\n")
for index, key in enumerate(sorted(res.keys()),start=1):
    keydict[index]=key
    sys.stdout.write("\t- %d : %s with %d reccords, linestyle : %s, marker : %s\n"%(index,key,len(res[key]),res[key][0].linestyle,res[key][0].marker))



buffer=""
print("q to quit, d 1 to delete reccord 1")
buffer=""
while buffer != "q\n":
    buffer=sys.stdin.readline()
    user_input=buffer.split()
    if len(user_input)>1:
        index=(int(user_input[1]))
        if keydict[index] in res :
            if user_input[0]=="d" and  len(user_input)==2:
                del res[keydict[index]]
                print(("reccord %s deleted" % keydict[index]))
                continue


            elif user_input[0] == "l" and  len(user_input)==3:
                res[keydict[index]][0].linestyle=user_input[2]
                print(("%s will be displayed with %s" % (keydict[index], user_input[2])))
                continue
            elif user_input[0] == "m" and  len(user_input)==3:
                res[keydict[index]][0].marker=user_input[2]
                print(("%s will be displayed with %s" % (keydict[index], user_input[2])))
                continue

            elif user_input[0] == "n" and  len(user_input)==3:
                v=res[keydict[index]]
                del res[keydict[index]]
                res[user_input[2]]=v
                continue
        else:
            print("error - no one here")




with open("results.pickle", "w") as f:
        pickle.dump(res,f)
        print("saved")

