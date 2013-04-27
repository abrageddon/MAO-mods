#!/usr/bin/python
import sys, os, string, shlex
import subprocess



if __name__ == '__main__':
    replay = open('recorded.make','r')
    currentDir = os.getcwd()
    cmdLine = ''
    multiline = False

    for line in replay:
        if multiline:
            cmdLine += line
        else:
            colon = line.find(":")
            if colon == -1: continue
            currentDir = line[:colon]
            cmdLine = line[colon+1:]


        if (cmdLine[-2] == '\\'):
            #print "MULTILINE " + cmdLine
            multiline=True
            continue
            
        multiline=False

        cmd = shlex.split(cmdLine)
	line = string.join(cmd[1:], ' ')
        #runIt = ['/bin/sh', '-c', 'echo', '"hello world"' ]
        #runIt = ['/bin/sh'] + shlex.split(cmdLine)
        #runIt = ['/bin/sh', '-c', line]
        runIt = ['/bin/sh'] + cmd
        print 'currentDir: ' + currentDir
        print 'cmdLine: /bin/sh ' + cmdLine.rstrip()
	print 'runIt: ' + str(runIt)
        #print 'cmdLine: /bin/sh ' + str(shlex.split(cmdLine.rstrip()) )
        #print 'cmdLine: /bin/sh ' + cmdLine.rstrip()

        process = subprocess.Popen(args=cmd, executable='/bin/sh', cwd=currentDir ,shell=True)
        #retCode = subprocess.call(runIt, cwd=currentDir )
        #retCode = subprocess.call(runIt, cwd=currentDir )
        #process = subprocess.call(cmdLine.rstrip(), shell=True, cwd=currentDir )
        #process = subprocess.Popen(cmdLine.rstrip(), shell=True, cwd=currentDir )
        #process = subprocess.Popen(runIt, shell=False, cwd=currentDir , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #process = subprocess.Popen('/bin/sh '+cmdLine, shell=True, cwd=currentDir )
        retCode = process.wait()
        if (retCode != 0):
	    sys.exit( retCode )


    replay.close()



