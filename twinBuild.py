#!/usr/bin/env python
import os, subprocess
from multiprocessing import Process

def makeIt(run):
  print run
  buildRets.append( subprocess.Popen(run) )

if __name__ == '__main__':
  buildDirs = ['SmallTestProgram', 'SmallTestProgram2']
  buildRets = []
  
  for instance in buildDirs:
    run = 'make -C '+instance
    print run
    p = Process(target=makeIt, args=(instance))
    p.start()
    buildRets.append(p)
  
  for rets in buildRets:
    p.join()

