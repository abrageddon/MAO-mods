#!/usr/bin/python
import sys, os, re, string, subprocess, shutil, random, getpass

def main():
    global prDebug
    global mkdirFlag
    global realBuild
    global doBuildObj
    global doBuildBlob
    global doDiv
    
    # output to std err
    prDebug=False
    # really make dirs, not just print
    mkdirFlag=True 
    # really build, not just print
    realBuild=True
    doBuildObj=False
    doBuildBlob=True
    doDiv=True
    
    
    global clangExec
    global gccExec
    global retCode
    global doExcludeBuild
    
    clangExec = 'clang'
    gccExec = 'gcc'
    retCode = 0
    doExcludeBuild = False

    # make args a single string
    #TODO pullout flags
    #TODO -buildObject explicit flag

    global compilerFlags
    global blobCompilerFlags
    global assemblerFlags
    global generateAssemblyFlags
    global sources
    global objects

    compilerFlags = sys.argv[1:]
    blobCompilerFlags = []
    assemblerFlags = []
    generateAssemblyFlags = []
    sources = []
    objects = []

    global rawFile
    global cachedFile
    global cacheDir
    global binFile
    global objFile
    rawFile=''
    cachedFile=''
    cacheDir=''
    binFile=''
    objFile=''
    
    
    global bcFile
    global blobS
    global blobSDiv
    
    
    #TODO pull seed and percent from commandline 
    # Pick the correct clang....
    if ('++' in sys.argv[0]):
        clangExec = 'clang++'
        gccExec = 'g++'
    
    global cmdLine
    cmdLine = ' ' + string.join(sys.argv[1:],' ') + ' '

    initVars(sys.argv[1:])


    # TODO make portable; raw compile configure
    if ( doExcludeBuild
         or bool(re.search(r'workspace/[^/]+/[^/]+\Z',os.getcwd())) #FIREFOX
         or bool(re.search(r'conftest\.?[ocC]*\s?',cmdLine)) #conf exempt
         or bool(re.search(r'/config/?',os.getcwd())) #FIREFOX
        ):
        excludeBuild()

    

    # name cached file
    #TODO REMOVE THESE 
    bcFile = cachedFile + ".bc"
    asmFile = cachedFile + ".s"
    blobS = cachedFile + ".blob.s"
    blobSDiv = cachedFile + ".blob.div.s"


    
    # There is an .o output file we want to cache
    if len(objFile)!=0:
        # determine location of cached bitcode
        if not doBuildObj or doBuildBlob:
            cacheBitcode(bcFile)

        if (doBuildObj):
            cacheAssembly(asmFile)
            diversify(asmFile+"Div.s", asmFile)
            useS=''
            if doDiv:
                useS = asmFile+"Div.s"
            else:
                useS = asmFile
            buildObjFromASM(objFile, useS)
    
    if  len(binFile)!=0:

        #TODO if compiling from .c to bin, do different build
        
        #if input is .c and input.bc doesn't exist; build input.c bitcode
        #if blob doesnt exist; use input.c as .bc

        if doBuildBlob:
            # Build blob object from bitcode
            linkAndCacheAssemblyBlob(blobS)
        
            #Diversify
            diversify(blobSDiv, blobS)

            useBlob=''
            if doDiv:
                useBlob = blobSDiv
            else:
                useBlob = blobS

            buildBinFromBlobS(binFile, useBlob)

        else:
            buildBinFromObjs()
        

    if len(objFile) == 0 and len(binFile) == 0:
        errorCatch(1,'No Output File','')

    if prDebug: sys.stderr.write( "\n" )
    sys.exit(retCode)


### FUNCTIONS ###

def cacheAssembly(output, inFile=None):
    if not os.path.isfile(output):
        if prDebug: sys.stderr.write ("=== Cache Assembly ===" +'\n\n')

        if doBuildObj:
            if(inFile is None):
                #assemble = [clangExec, '-o', output] + generateAssemblyFlags
                assemble = [gccExec, '-o', output] + generateAssemblyFlags + sources
            else:
                #assemble = [clangExec, '-o', output, '-S', inFile]
                assemble = [gccExec, '-o', output, '-S', inFile]
        else:
            assemble = [clangExec, "-o", output, "-S", inFile] + generateAssemblyFlags

        if prDebug: sys.stderr.write (string.join(assemble,' ')+'\n\n')
        return execBuild(assemble, "Cache Assembly")
    return retCode
    
    
def diversify(output, inFile):
    if doDiv:
        if prDebug: sys.stderr.write ("=== Diversify ===" +'\n\n')
        
        #TODO read from command line and purge after use
        #seed = str(random.randint(0,100000))
        #percent = str(random.randint(10,50))
        seed = '1234567890'
        percent = '30'
        
        tests = ""
        
        #tests += "--plugin=/usr/local/lib/MaoSchedRand-x86_64-linux.so:SCHEDRAND=MultiCompilerSeed["+seed+"]+ISchedRandPercentage["+percent+"]:"
        tests += "--plugin=/usr/local/lib/MaoMOVToLEA-x86_64-linux.so:MOVTOLEA=MultiCompilerSeed["+seed+"]+MOVToLEAPercentage["+percent+"]:"
        tests += "--plugin=/usr/local/lib/MaoNOPInsertion-x86_64-linux.so:NOPINSERTION=MultiCompilerSeed["+seed+"]+NOPInsertionPercentage["+percent+"]:"        
        
        diversify = ["mao", "--mao="+tests+"ASM=o["+output+"]", inFile ]
        
        #TODO TIME THIS STEP
        if prDebug: sys.stderr.write (string.join(diversify,' ')+'\n\n')
        return execBuild(diversify, "Diversify")
    return retCode


def buildObjFromASM(output, inFile):
    if prDebug: sys.stderr.write ("=== ASM To Obj ===" +'\n\n')

    #buildObj = [gccExec, '-Wa', inFile, '-o', output]+ buildObj.strip().split(' ')
    #TODO explore using 'as' further
    buildObj = ['as', inFile, '-o', output] + assemblerFlags

    #TODO TIME THIS STEP
    if prDebug: sys.stderr.write (string.join(buildObj,' ')+'\n\n')
    return execBuild(buildObj,"ASM To Obj")


def buildBinFromObjs():
    if prDebug: sys.stderr.write ("=== Build Bin From Objs ===" +'\n\n')

    buildBin = [gccExec] + compilerFlags
    #buildBin = ['gold'] + compilerFlags
    #buildBin = ['ld.gold'] + compilerFlags

    #TODO TIME THIS STEP
    if prDebug: sys.stderr.write (string.join(buildBin,' ')+'\n\n')
    return execBuild(buildBin, "Build Bin From Objs")
    


### BLOB FUNCTIONS ###

def cacheBitcode(output, inFile=None):    # Build .bc file if there is no cached version
    if ( not os.path.isfile(output) ):        
        if prDebug: sys.stderr.write ("=== To Bitcode Cache ===" +'\n\n')
        
        if(inFile is None):
            buildBc = [clangExec, '-o', output, '-emit-llvm'] + generateAssemblyFlags + sources
        else:
            buildBc = [clangExec, '-o', output, '-S', '-emit-llvm', inFile]
        
        return execBuild(buildBc,"To Bitcode Cache")
    return retCode

def linkAndCacheAssemblyBlob(output):
    global retCode
    if not os.path.isfile(output):
        if prDebug: sys.stderr.write ("=== Linking Bitcode Files ===" +'\n\n')

        #TODO change directory to do less file rewriting, might cause cmd line to get too long
        inObj = objects
        inSrc = sources
        
        #For each obj .o located cached .bc file
        for i,item in enumerate(objects):
            inObj[i] = cacheDir + "/" + item[:-1] + 'bc'
        
        for i,item in enumerate(sources):
            inSrc[i] = cacheDir + "/" + re.sub(r'\.[cCsS]+[pPxX+]*','.bc',item)
            cacheBitcode(inSrc[i], item)

        blobBc = output + ".bc"
        llvmLink = ["llvm-link", "-S", "-o", blobBc] + inObj + inSrc
        retCode = execBuild(llvmLink, "Linking Bitcode Files") and retCode
        
        if retCode == 0:
	          return cacheAssembly(output, blobBc);
    return retCode

def buildBinFromBlobS(output, inFile):
    if retCode == 0:
        if prDebug: sys.stderr.write ("=== Build Bin From BlobS ===" +'\n\n')

        #TODO figure out how to build final bin
        buildBin = ['as', "-o", output, inFile]
        #buildBin = [gccExec, '-Wa', "-o", output, inFile] + blobCompilerFlags
        #buildBin = [gccExec, "-Wa,-alh,-L", "-o", output, inFile] + string.split(flags.strip(),' ')
        #buildBin = [clangExec, "-o", output, inFile] + string.split(flags,' ')

        if prDebug: sys.stderr.write (string.join(buildBin,' ')+'\n\n')
        return execBuild(buildBin, "Build Bin From BlobS")
    return retCode
    
### UTILITIES ###

def execBuild(cmd, mesg):
    global retCode
    if realBuild:
        process = subprocess.Popen(cmd)
        retCode = process.wait()
    return errorCatch(retCode, string.join(cmd,' '), mesg)
    
def failBuild():
    # Something didn't work. Fail back to compile from scratch.
    if prDebug: sys.stderr.write ("=== Fail Build Attempt ===" +'\n\n')
    return execBuild([clangExec] +  cmdLine.strip().split(), "Fail Build")
    
def excludeBuild():
    # Something didn't work. Fail back to compile from scratch.
    if prDebug: sys.stderr.write ("=== Excluded Build Attempt ===" +'\n\n')
    #retCode = execBuild([gccExec] + compilerFlags, "Excluded Build")
    retCode = execBuild([clangExec] + compilerFlags, "Excluded Build")
    sys.exit(retCode)

def errorCatch(retCode, cmd, mesg):
    if (retCode != 0):
        sys.stderr.write ('========= Error: '+ mesg +' failed\n'+cmd+'\n\n')
        sys.stderr.write( 'os.getcwd(): '+ os.getcwd() +'\n\n')
        sys.stderr.write( 'cmdLine: '+ cmdLine +'\n\n')
        sys.stderr.write( 'rawFile: ' + rawFile +'\n')
        sys.stderr.write( 'cachedFile: ' + cachedFile +'\n')
        sys.stderr.write( 'objFile: ' + objFile +'\n')
        sys.stderr.write( 'binFile: ' + binFile +'\n\n')
        
        sys.stderr.write( 'compilerFlags: ' + str(compilerFlags) +'\n\n')
        sys.stderr.write( 'generateAssemblyFlags: ' + str(generateAssemblyFlags) +'\n\n')
        sys.stderr.write( 'assemblerFlags: ' + str(assemblerFlags) +'\n\n')
        sys.stderr.write( 'blobCompilerFlags: ' + str(blobCompilerFlags) +'\n\n')
        
        sys.stderr.write( 'sources: ' + str(sources) +'\n')
        sys.stderr.write( 'objects: ' + str(objects) +'\n\n')
        #TODO failBuild?
        sys.exit(retCode)
    return retCode


def initVars(varList):
    global rawFile
    global cachedFile
    global cacheDir
    global objFile
    global binFile
    
    global compilerFlags
    global blobCompilerFlags
    global assemblerFlags
    global generateAssemblyFlags
    global sources
    global objects
    global doBuildObj
    global doExcludeBuild
    
    isOutput = False
    isCompGen = False
    
    generateAssemblyFlags += ['-S']

    buildObjList = ["host_stdc++compat.o", "stdc++compat.o", "bignum-dtoa.o"
        , "bignum.o", "cached-powers.o", "diy-fp.o", "double-conversion.o"
        , "fast-dtoa.o", "fixed-dtoa.o", "strtod.o", "HashFunctions.o", "jemalloc.o"
        , "extraMallocFuncs.o", "adler32.o", "compress.o", "crc32.o", "deflate.o"
        , "gzclose.o", "gzlib.o", "gzread.o", "gzwrite.o", "infback.o", "inffast.o"
        , "inflate.o", "inftrees.o", "trees.o", "ncompr.o", "dummy.o", "zutil.o"
        , "prvrsion.o", "prfdcach.o", "prmwait.o", "prmapopt.o", "priometh.o"
        , "pripv6.o", "prlayer.o", "prlog.o", "prmmap.o", "prpolevt.o", "prprf.o"
        , "prscanf.o", "prstdio.o", "prcmon.o", "prrwlock.o", "prtpd.o", "prlink.o"
        , "prmalloc.o", "prmem.o", "prosdep.o", "prshm.o", "prshma.o", "prseg.o"
        , "pralarm.o", "pratom.o", "prcountr.o", "prdtoa.o", "prenv.o", "prerr.o"
        , "prerror.o", "prerrortable.o", "prinit.o", "prinrval.o", "pripc.o"
        , "prlog2.o", "prlong.o", "prnetdb.o", "praton.o", "prolock.o", "prrng.o"
        , "prsystem.o", "prthinfo.o", "prtpool.o", "prtrace.o", "prtime.o"
        , "ptsynch.o", "ptio.o", "ptthread.o", "ptmisc.o", "unix.o", "unix_errors.o"
        , "uxproces.o", "uxrng.o", "uxshm.o", "uxwrap.o", "linux.o", "os_Linux_x86_64.o"
        ]

    for var in varList:
        #Final compile must be ordered specifically
        #compilerFlags += [var]
# adler32.o compress.o crc32.o deflate.o gzclose.o gzlib.o gzread.o gzwrite.o infback.o inffast.o inflate.o inftrees.o trees.o uncompr.o zutil.o
        
        if isOutput:
            if var[-2:] == '.o':
                #FIREFOX
                #Objects explicitly needed
                for item in buildObjList:
                    if ( item in var):
                        doBuildObj = True

                objFile = var
                rawFile = var[:-2]
            else:
                binFile = var
                rawFile = var
                
            isOutput = False
            continue
        
        if isCompGen:
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            isCompGen=False
            continue
                
        # Exclude from genAssembly     -D_FORTIFY_SOURCE=1

#TODO add seed, percent, debug flags to be read from commandline    
#    if (sys.argv[1] == "-prDebug"):prDebug = True


        if var == '':
            continue
        #FLAGS
        elif var == '-E':
            doExcludeBuild = True
        elif var == '-S':
            doExcludeBuild = True
        elif (var[:16] == '-print-prog-name'
            or var == '-print-search-dirs'
            or var == '-print-multi-os-directory'):
            doExcludeBuild = True
        elif (var == '-v' or var == '-V' 
            or var == '--version' 
            or var == '-qversion' 
            or var == '-dumpversion'):
            doExcludeBuild = True
        elif var == '-Qunused-arguments':
            #-Qunused-arguments caused problems and is therefore ...unused...
            continue
        elif var == '-include':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            isCompGen = True
        elif (var[:4] == '-std'
            or var == '-pthread'
            or var == '-pedantic'
            or var == '-pipe'
            ):
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-L':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-D':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-O':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-I':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-W':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-f':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-l':
            #compilerFlags = ['-L/usr/local/lib', '-L/lib/x86_64-linux-gnu', '-L/usr/lib/x86_64-linux-gnu'] + compilerFlags
            blobCompilerFlags += [var]
            assemblerFlags += [var]
        elif var == '-o':
            isOutput = True
            continue
        elif var == '-c':
            pass
            blobCompilerFlags += [var]
        elif var[:1] == '-':
            addFlagsAll(var)
        #FILES    
        elif (var[-2:] == '.c' or var[-2:] == '.C' 
            or var[-3:] == '.cc' or var[-3:] == '.CC' 
            or var[-4:] == '.cpp' or var[-4:] == '.cpp' 
            or var[-4:] == '.CPP' or var[-4:] == '.CPP' 
            or var[-4:] == '.cxx' or var[-4:] == '.cxx' 
            or var[-4:] == '.CXX' or var[-4:] == '.CXX'):
            sources += [var]
        elif (var[-3:] == '.pp' or var[-3:] == '.PP'  or var[-2:] == '.a'):
            #FIREFOX
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif (var[-2:] == '.s' or var[-2:] == '.S'):
            sources += [var]
        elif (var[-2:] == '.o' or var[-2:] == '.O'):
            objects += [var]
        else:
            #addFlagsAll(var)
            errorCatch(1,var,'initVars')
    
    
        # TODO make portable; raw compile configure
#    if (
#         or bool(re.search(r'\sconftest\.[ocC]?\s',cmdLine)) #conf exempt
#         or bool(re.search(r'/config/?',os.getcwd())) #config folder exempt
#       ):
    
    
    
    if len(binFile)!=0 and len(sources)!=0 :
        if len(sources) == 1 :
            objFile = re.sub(r'\.[cCsS]+[^o]?[pPxX+]*','.o',os.path.basename(sources[0]))
            rawFile = objFile[:-2]
    
    if len(binFile)==0 and len(objFile)==0 :
        binFile = 'a.out'
    
    rawFile = os.path.realpath(rawFile)
    cachedFile = re.sub(r'/home/'+getpass.getuser()+r'/workspace/','/home/'+getpass.getuser()+r'/workspace/bcache/',rawFile)

    # make path to file if needed
    cacheDir = os.path.dirname(cachedFile)
    if cacheDir != '':
        if not os.path.isdir(cacheDir) :
            if mkdirFlag :
                try:
                    os.makedirs(cacheDir)
                except:
                    pass
            else:
                sys.stderr.write ('mkdir file\'s dir: '+cacheDir +'\n')
                
    
    
    #DEBUG
    #errorCatch(1,'Testing initVars','initVars')
    
    
def addFlagsAll(flag):
    global blobCompilerFlags
    global assemblerFlags
    global generateAssemblyFlags
    blobCompilerFlags += [flag]
    assemblerFlags += [flag]
    generateAssemblyFlags += [flag]
    

if __name__ == "__main__":
    main()
