#!/usr/bin/python
import sys, os, re, string, subprocess, shutil, random, getpass

def main():
    global prDebug
    global mkdirFlag
    global realBuild
    global doBuildObj
    global doBuildBlob
    global doDiv
    global useMAO
    
    # output to std err
    prDebug=False
    # really make dirs, not just print
    mkdirFlag=True 
    # really build, not just print
    realBuild=True

    doBuildObj=True
    doBuildBlob=False
    doDiv=True
    useMAO=True
    
    
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
    global assemblys
    global objects

    compilerFlags = []
    blobCompilerFlags = []
    assemblerFlags = []
    generateAssemblyFlags = []
    sources = []
    assemblys = []
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
         #or bool(re.search(r'workspace/[^/]+/[^/]+\Z',os.getcwd())) #FIREFOX
         or bool(re.search(r'conftest\.?[ocC]*\s?',cmdLine)) #conf exempt
         or bool(re.search(r'/config/?',os.getcwd())) #FIREFOX
        ):
        excludeBuild()

    

    # name cached file
    #TODO REMOVE THESE 
    bcFile = cachedFile + ".bc"
    asmFile = cachedFile + ".s"
    annotatedAsmFile = cachedFile + ".a.s"
    blobS = cachedFile + ".blob.s"
    blobSDiv = cachedFile + ".blob.div.s"


    
    # There is an .o output file we want to cache
    if len(objFile)!=0:
        # determine location of cached bitcode
        if not doBuildObj or doBuildBlob:
            cacheBitcode(bcFile)

        if (doBuildObj):
            cacheAssembly(asmFile)

	    if useMAO:
	        annotate(annotatedAsmFile, asmFile)
                diversify(cachedFile+".div.s", annotatedAsmFile)
            else:
                diversifyClang(asmFile+"div.s", bcFile)

            useS=''
            if doDiv:
                useS = cachedFile+".div.s"
            else:
                useS = asmFile
            buildObjFromASM(objFile, useS)
    
    if  len(binFile)!=0:

        #TODO if compiling from .c to bin, do different build
        
        #if input is .c and input.bc doesn't exist; build input.c bitcode
        #if blob doesnt exist; use input.c as .bc

        #TODO CORRECT THIS PART FOR DIVANNO
        if doBuildBlob:
            # Build blob object from bitcode
            linkAndCacheAssemblyBlob(blobS)
        
            #Diversify
	    if useMAO:
                diversify(blobSDiv, blobS)
            else:
                diversifyClang(blobSDiv, blobS+".bc")

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
    global retCode
    if not os.path.isfile(output):
        if prDebug: sys.stderr.write ("=== Cache Assembly ===" +'\n\n')

        if doBuildObj:
            if(inFile is None):
	        if len(sources) == 0:
		    return retCode

		if len(sources) == 1 and sources[0][-2:] == '.S' :
                    assemble = [gccExec, '-o', output, '-S'] + generateAssemblyFlags + sources
                    if realBuild:
		        outputFile = open(output, "w")
                        process = subprocess.Popen(assemble,stdout=outputFile)
                        retCode = process.wait()
                    return errorCatch(retCode, string.join(assemble,' '), 'Parsing .S File')
		else:
                    #assemble = [clangExec, '-o', output] + generateAssemblyFlags + sources
                    assemble = [gccExec, '-o', output, '-S'] + generateAssemblyFlags + sources
            else:
                #assemble = [clangExec, '-o', output, '-S', inFile]
                assemble = [gccExec, '-o', output, '-S', inFile]
        else:
            if(inFile is None):
	        if len(sources) == 0:
		    return retCode
                assemble = [clangExec, "-o", output, "-S"] + generateAssemblyFlags + sources
	    else:
                assemble = [clangExec, "-o", output, "-S", inFile] + generateAssemblyFlags

        if prDebug: sys.stderr.write (string.join(assemble,' ')+'\n\n')
        return execBuild(assemble, "Cache Assembly")
    return retCode
    
def diversify(output, inFile):
    #TODO use output file name
    if doDiv:
        if prDebug: sys.stderr.write ("=== Diversify ===" +'\n\n')
        diversify = ["divanno", inFile ]
        
        if prDebug: sys.stderr.write (string.join(diversify,' ')+'\n\n')
        return execBuild(diversify, "Diversify")


def annotate(output, inFile):
    if os.path.isfile(output):
        return retCode
    if prDebug: sys.stderr.write ("=== Annotate ===" +'\n\n')
        
    #TODO read from command line and purge after use
    tests = ""
    
    #tests += "--plugin=/usr/local/lib/MaoSchedRand-x86_64-linux.so:SCHEDRAND=MultiCompilerSeed["+seed+"]+ISchedRandPercentage["+percent+"]:"
    tests += "--plugin=/usr/local/lib/MaoMOVToLEAAnnotate-x86_64-linux.so:MOVTOLEAA:"
    tests += "--plugin=/usr/local/lib/MaoNOPInsertionAnnotate-x86_64-linux.so:NOPINSERTIONA:"        
    
    annotate = ["mao", "--mao="+tests+"ASM=o["+output+"]", inFile ]
        
    if prDebug: sys.stderr.write (string.join(annotate,' ')+'\n\n')
    return execBuild(annotate, "Annotate")

def diversifyClang(output, inFile):
    if doDiv:
        if prDebug: sys.stderr.write ("=== Diversify ===" +'\n\n')

        #TODO read from command line and purge after use
        #seed = str(random.randint(0,100000))
        #percent = str(random.randint(10,50))
        seed = '1234567890'
        percent = '30'

        tests = ["-Xclang", "-multicompiler-seed="+seed, "-Xclang", "-nop-insertion-percentage="+percent]

        diversify = [clangExec, "-S", "-o", output, inFile ] + tests

        #TODO TIME THIS STEP
        if prDebug: sys.stderr.write (string.join(diversify,' ')+'\n\n')
        return execBuild(diversify, "Diversify")
    return retCode


def buildObjFromASM(output, inFile):
    if prDebug: sys.stderr.write ("=== ASM To Obj ===" +'\n\n')

    buildObj = [gccExec, '-Wa', '-c', inFile, '-o', output] + blobCompilerFlags
    #buildObj = [gccExec, '-Wa', inFile, '-o', output] + blobCompilerFlags
    #TODO explore using 'as' further
    #buildObj = ['as', inFile, '-o', output] + assemblerFlags

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
        buildBc = ''
        if(inFile is None):
            if len(sources)!=0:
                buildBc = [clangExec, '-o', output, '-S', '-emit-llvm'] + generateAssemblyFlags + sources
        else:
            buildBc = [clangExec, '-o', output, '-S', '-emit-llvm', inFile]
        
        if len(buildBc)==0:
            return retCode
        if prDebug: sys.stderr.write (string.join(buildBc,' ')+'\n\n')
        return execBuild(buildBc,"To Bitcode Cache")
    return retCode

def linkAndCacheAssemblyBlob(output):
    global retCode
    if not os.path.isfile(output):
        if prDebug: sys.stderr.write ("=== Linking Bitcode Files ===" +'\n\n')

        inObj = [None] * len(objects)
        inSrc = [None] * len(sources)
        
        #For each obj .o located cached .bc file
        for i,item in enumerate(objects):
            inObj[i] = cacheDir + "/" + item[:-1] + 'bc'
        
        for i,item in enumerate(sources):
	    cacheThis = item
            inSrc[i] = cacheDir + "/" + re.sub(r'\.[cC]+[pPxX+]*','.bc',item)
            cacheBitcode(inSrc[i], cacheThis)

        blobBc = output + ".bc"
        llvmLink = ["llvm-link", "-S", "-o", blobBc] + inObj + inSrc

        if prDebug: sys.stderr.write (string.join(llvmLink,' ')+'\n\n')
        retCode = execBuild(llvmLink, "Linking Bitcode Files") and retCode
        
        if retCode == 0:
            return cacheAssembly(output, blobBc);
    return retCode

def buildBinFromBlobS(output, inFile):
    global retCode
    if retCode == 0:
        if prDebug: sys.stderr.write ("=== Build Bin From BlobS ===" +'\n\n')

        #TODO figure out how to build final bin
        #buildBin = ['as', "-o", output, inFile]
        buildBin = [gccExec, '-Wa', "-o", output, inFile] + blobCompilerFlags
        #buildBin = [gccExec, "-Wa,-alh,-L", "-o", output, inFile] + blobCompilerFlags
        #buildBin = [clangExec, "-o", output, inFile] + blobCompilerFlags

        if prDebug: sys.stderr.write (string.join(buildBin,' ')+'\n\n')
	retCode = execBuild(buildBin, "Build Bin From BlobS") and retCode
	os.chmod(output, 0775)
        return retCode
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
        sys.stderr.write( 'assemblys: ' + str(assemblys) +'\n')
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
    global assemblys
    global objects
    global doBuildObj
    global doBuildBlob
    global doExcludeBuild
    
    isOutput = False
    isCompGen = False

    for var in varList:
        #Final compile must be ordered specifically

        #-Qunused-arguments caused problems and is therefore ...unused...
	if var == '-Qunused-arguments':
            continue


	compilerFlags += [var]

        
        if isOutput:
            if var[-2:] == '.o':
                objFile = var
                rawFile = var[:-2]
            elif var[-3:] == '.so':
                binFile = var
                rawFile = var[:-3]
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
        elif var == '-include' or var == '--param':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            isCompGen = True
        elif (var[:4] == '-std'
            or var == '-pthread'
            or var == '-pedantic'
            or var == '-pipe'
            or var == '-msse'
            or var == '-m64'
            or var == '-mmmx'
            or var == '-mssse3'
            or var == '-ansi'
            or var == '-use-gold-plugin'
            ):
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-L':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var[:2] == '-D' or var[:2] == '-U':
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
            #blobCompilerFlags += [var]
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
        elif (var[-2:] == '.S'):
	    #TODO preprocess .S
	    sources += [var]
        elif (var[-3:] == '.pp' or var[-3:] == '.PP'  or var[-2:] == '.a' or var[-3:] == '.so' or var[-3:] == '.SO'):
            #FIREFOX
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif (var[-2:] == '.s'):
            assemblys += [var]
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
    
    generateAssemblyFlags += ['-fPIC']
    compilerFlags += ['-fPIC']
    
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
                
    
    #Copy assembly files now to save time later
    for item in assemblys:
        asmFile = os.path.realpath(item)
        cmd = ['cp', item, cachedFile+'.s' ]
        if realBuild:
            process = subprocess.Popen(cmd)
            retCode = process.wait()
        return errorCatch(retCode, string.join(cmd,' '), 'Copy Existing Assembly')
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
