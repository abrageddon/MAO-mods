#!/usr/bin/python
import sys, os, string
import subprocess

debugOut = False

if __name__ == '__main__':
    
    runProg = sys.argv[1:]
#    print ["sh"] + runProg
    out = open('/home/ubuntu/recorded.make','a')
    out.write(os.getcwd()+':'+string.join(runProg,' ')+"\n")
    out.close()
    
    subprocess.call(["sh"]+runProg)
    
    
