#!/usr/bin/python
import time, sys, re
import subprocess

debugOut = False

if __name__ == '__main__':
    progName = "Unknown"
    
#    sys.stderr.write(str(sys.argv)+"\n")
    
    for i in range(len(sys.argv)):
#        sys.stderr.write(sys.argv[i]+"\n")
        #skip self
        if i == 0:
            continue
        #skip sh flags
        if ( bool(re.search(r'^[^-]',sys.argv[i])) ):#TODO better way to find what the executable is
            if ( bool(re.search(r'libtool\b',sys.argv[i])) ):# identify libtool, nsinstall, python, clang[++]
                
                sys.stderr.write("libtool:::"+sys.argv[i]+"\n")

                compiler = ""
                if ( bool(re.search(r'(b|MAO)?[^X]clang\+\+',sys.argv[i])) ):
                    compiler = "clang++"
                elif ( bool(re.search(r'(b|MAO)?[^X]clang',sys.argv[i])) ):#TODO VERIFY
                    compiler = "clang"                    
                progName = "libtool " + compiler
                break
            if ( bool(re.search(r'(b|MAO)?[^X]clang\+\+',sys.argv[i])) ):
                progName = "clang++"
                break
            if ( bool(re.search(r'(b|MAO)?[^X]clang',sys.argv[i])) ):
                progName = "clang"
                break
            sp = sys.argv[i].split()
            #find first word of input and use that as the executable name
            for j in range( len(sp) ):
                if ( bool(re.search(r'python\b',sp[j])) ):
                    script = ""
                    if (i < len(sp)):
                        script = sp[j+1]
                    else:
                        script = sys.argv[i+1]
                    progName = "python " + re.sub(r'.*/',r'',script)
                    break
                if ( bool(re.search(r'nsinstall\b',sp[j])) ):
                    progName = "nsinstall"
                    break
                
                if ( bool(re.search(r'^[./\w]',sp[j])) ):
                    #TODO if contains = then skip
                    if ( "=" in sp[j]
                      or "'" in sp[j]
                      or "timesh.py" in sp[j]
                      or "if" == sp[j]):
                        continue
                    progName = re.sub(r'.*/',r'',sp[j])
                    break
        if progName != "Unknown":
            break
#    sys.stderr.write(progName+"\n\n")
    
    runProg = sys.argv[1:]
#    print ["sh"] + runProg
    
    startTime = time.time()
    subprocess.call(["sh"]+runProg)
    endTime = time.time()
    
    
    out = open('/home/ubuntu/report.timesh','a')
#    out = open('report.timesh','a')
    out.write(progName+":"+ str(endTime - startTime)+"\n")
    out.close()
#    print progName+":"+ str(endTime - startTime)+" Seconds"
