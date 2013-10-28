#!/usr/bin/python
import sys, os, re, string, subprocess, shutil, random, getpass, pickle, time

# output to std err
prDebug=True
#prDebug=False
# really make dirs, not just print
mkdirFlag=True 
# really build, not just print
realBuild=True
doDiv=True
useMAO=True

#doBuildObj=True ; doBuildBlob=False
doBuildObj=False ; doBuildBlob=True
#doBuildObj=True ; doBuildBlob=True

extraFlags = []
#extraFlags = ['-time', '-ftime-report'] ; prDebug=True




clangExec = 'clang'
gccExec = 'gcc'
retCode = 0
doExcludeBuild = False
Moverride = False
isAsm = False

compilerFlags = []
blobCompilerFlags = []
assemblerFlags = []
generateAssemblyFlags = []
generateAssemblyCacheFlags = []
divannoFlags = []

sources = []
assemblys = []
objects = []
archives = []

rawFile=''
cachedFile=''
cacheDir=''
binFile=''
objFile=''
MFile=''
MCacheFile=''

seed=""
percent=0

#user = 'sneisius'
user = getpass.getuser()

def main():
    global timeTest
    timeTest = time.time()

    global retCode

    
    
    #TODO pull seed and percent from commandline 
    # Pick the correct clang....
    if ('++' in sys.argv[0]):
        global clangExec
        global gccExec
        clangExec = 'clang++'
        gccExec = 'g++'
    
    global cmdLine
    cmdLine = ' ' + string.join(sys.argv[1:],' ') + ' '
    #print cmdLine

    initVars(sys.argv[1:])


    # TODO make portable; raw compile configure
    if ( doExcludeBuild
         or bool(re.search(r'conftest\.?[ocC]*\s?',cmdLine)) #conf exempt
         or bool(re.search(r'/config/?',os.getcwd())) #FIREFOX
    #     or bool(re.search(r'workspace/[^/]+/[^/]+\Z',os.getcwd())) #FIREFOX
        ):excludeBuild()

    

    # name cached file
    #TODO REMOVE THESE 
    global bcFile
    global asmFile
    global annotatedAsmFile
    global blobS
    global blobSDiv
    global annotatedAsmBlobFile
    bcFile = cachedFile + ".bc"
    asmFile = cachedFile + ".s"
    annotatedAsmFile = cachedFile + ".a.s"
    blobS = cachedFile + ".blob.s"
    blobSDiv = cachedFile + ".blob.div.s"
    annotatedAsmBlobFile = cachedFile + ".blob.a.s"


    
    #print "TIME TO INIT: "+ str(time.time() - timeTest)
    # There is an .o output file we want to cache
    if len(objFile)!=0:
        # determine location of cached bitcode
        #cacheBitcode(bcFile)#TEMP
        if not doBuildObj or doBuildBlob:
            cacheBitcode(bcFile)
            if (Moverride and not os.path.isfile(MCacheFile)):
                if prDebug: sys.stderr.write ("=== -M Override ===" +'\n\n')
                cmd = ['cp', MFile, MCacheFile]
                if prDebug: sys.stderr.write (string.join(cmd,' ')+'\n\n')
                if realBuild:
                    process = subprocess.Popen(cmd)
                    retCode = process.wait()
                retCode = errorCatch(retCode, string.join(cmd,' '), 'Cache -M Output')

        if (doBuildObj):
            cacheAssembly(asmFile)

            if (Moverride and not os.path.isfile(MCacheFile)):
                if prDebug: sys.stderr.write ("=== -M Override ===" +'\n\n')
                cmd = ['cp', MFile, MCacheFile]
                if prDebug: sys.stderr.write (string.join(cmd,' ')+'\n\n')
                if realBuild:
                    process = subprocess.Popen(cmd)
                    retCode = process.wait()
                retCode = errorCatch(retCode, string.join(cmd,' '), 'Cache -M Output')

            useS=''
            if doDiv:
                if useMAO:
                    annotate(annotatedAsmFile, asmFile)
                    diversify(cachedFile+".div.s", annotatedAsmFile)
                else:
                    diversifyClang(asmFile+"div.s", bcFile)

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
                annotate(annotatedAsmBlobFile, blobS)
                diversify(blobSDiv, annotatedAsmBlobFile)
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

    if prDebug: sys.stderr.write( "MAOclang RUNTIME: "+ str(time.time() - timeTest) +'\n')
    if prDebug: sys.stderr.write( "\n" )
    sys.exit(retCode)


### FUNCTIONS ###

def cacheAssembly(output, inFile=None):
    global retCode
    global Moverride
    if ( os.path.isfile(output) ):
        if (Moverride and os.path.isfile(MCacheFile) ):
        #TODO cache this!
            if prDebug: sys.stderr.write ("=== -M Override ===" +'\n\n')
            cmd = ['cp', MCacheFile, MFile]
            if prDebug: sys.stderr.write (string.join(cmd,' ')+'\n\n')
            if realBuild:
                process = subprocess.Popen(cmd)
                retCode = process.wait()
            return errorCatch(retCode, string.join(cmd,' '), 'Copy -M Output')
        return retCode

    if prDebug: sys.stderr.write ("=== Cache Assembly ===" +'\n\n')

    if doBuildObj:
        if(inFile is None):
            if len(sources) == 0:
                return retCode

            if len(sources) == 1 and sources[0][-2:] == '.S' :
                if prDebug: sys.stderr.write ("=== Cache S Assembly ===" +'\n\n')
                assemble = [gccExec, '-o', output, '-S'] + generateAssemblyFlags + sources
                if prDebug: sys.stderr.write (string.join(assemble,' ')+'\n\n')
                if realBuild:
                    outputFile = open(output, "w")
                    process = subprocess.Popen(assemble,stdout=outputFile)
                    retCode = process.wait()
                return errorCatch(retCode, string.join(assemble,' '), 'Parsing .S File')
            else:
                assemble = [gccExec, '-o', output, '-S'] + generateAssemblyFlags + sources
        else:
            #From BC
            #TODO flag to add -fPIC if output is .so
            assemble = [clangExec, '-fPIC', '-o', output, '-S', inFile]
            #assemble = [gccExec, '-o', output, '-S', inFile] #+ generateAssemblyFlags
    else:
        if(inFile is None):
            if len(sources) == 0:
                return retCode
            assemble = [clangExec, "-o", output, "-S"] + generateAssemblyFlags + sources
        else:
            #TODO flag to add -fPIC if output is .so
            assemble = [clangExec, '-fPIC', "-o", output, "-S", inFile] + generateAssemblyFlags

    if prDebug: sys.stderr.write (string.join(assemble,' ')+'\n\n')
    return execBuild(assemble, "Cache Assembly")
    
def diversify(output, inFile):
    #TODO use output file name
    if not doDiv:
        return retCode
    if prDebug: sys.stderr.write ("=== Diversify ===" +'\n\n')
    diversify = ["divanno", "-f", inFile , "-o", output, "-seed", str(seed), "-percent", str(percent) ] + divannoFlags
        
    if prDebug: sys.stderr.write (string.join(diversify,' ')+'\n\n')
    return execBuild(diversify, "Diversify")


def annotate(output, inFile):
    if os.path.isfile(output):
        return retCode
    if prDebug: sys.stderr.write ("=== Annotate ===" +'\n\n')
        
    #TODO read from command line and purge after use
    tests = ""
    
    tests += "--plugin=/usr/local/lib/MaoSchedAnnotate-x86_64-linux.so:SCHEDA:"
    #tests += "--plugin=/usr/local/lib/MaoSchedRand-x86_64-linux.so:SCHEDRAND=MultiCompilerSeed["+seed+"]+ISchedRandPercentage["+percent+"]:"
    tests += "--plugin=/usr/local/lib/MaoMOVToLEAAnnotate-x86_64-linux.so:MOVTOLEAA:"
    tests += "--plugin=/usr/local/lib/MaoNOPInsertionAnnotate-x86_64-linux.so:NOPINSERTIONA:"        
    tests += "--plugin=/usr/local/lib/MaoLabelAll-x86_64-linux.so:LABELALL:"
    
    annotate = ["mao", "--mao="+tests+"ASM=o["+output+"]", inFile ]
        
    if prDebug: sys.stderr.write (string.join(annotate,' ')+'\n\n')
    return execBuild(annotate, "Annotate")

def diversifyClang(output, inFile):
    if doDiv:
        if prDebug: sys.stderr.write ("=== Diversify ===" +'\n\n')

        #TODO read from command line and purge after use
        #seed = str(random.randint(0,100000))
        #percent = str(random.randint(10,50))
        #seed = '1234567890'
        #percent = '30'

        tests = ["-Xclang", "-multicompiler-seed="+seed, "-Xclang", "-nop-insertion-percentage="+percent]

        diversify = [clangExec, "-S", "-o", output, inFile ] + tests

        #TODO TIME THIS STEP
        if prDebug: sys.stderr.write (string.join(diversify,' ')+'\n\n')
        return execBuild(diversify, "Diversify")
    return retCode


def buildObjFromASM(output, inFile):
    if prDebug: sys.stderr.write ("=== ASM To Obj ===" +'\n\n')

    #buildObj = [clangExec, '-o', output, '-c'] + assemblerFlags + [inFile]
    #buildObj = [gccExec, '-o', output, '-c'] + blobCompilerFlags + [inFile]
    buildObj = [gccExec, '-o', output, '-c'] + assemblerFlags + [inFile]
    #buildObj = [gccExec, '-Wa', '-c', inFile, '-o', output] + assemblerFlags
    #buildObj = [gccExec, '-Wa', inFile, '-o', output] + blobCompilerFlags
    #TODO explore using 'as' further
    #buildObj = ['as', inFile, '-o', output] + assemblerFlags


    #TODO TIME THIS STEP
    if prDebug: sys.stderr.write (string.join(buildObj,' ')+'\n\n')
    return execBuild(buildObj,"ASM To Obj")


def buildBinFromObjs():
    if prDebug: sys.stderr.write ("=== Build Bin From Objs ===" +'\n\n')

    # if archive THEN store -l flags
    addFlags = []
        #addFlags = ['-I.', '-I..', '-I../gnu', '-I../', '-I../gnu', '-I../lib']
    arLibs = set()
    for ar in archives:
        arCache =  os.path.realpath(str(ar[:-2])+'.libs')
        arCache = re.sub(r'/home/'+user+r'/workspace/','/home/'+user+r'/workspace/bcache/',arCache)
        #print "AR: " + arCache
        arLibs = set(libs)
        if os.path.isfile(arCache):
            with open(arCache, 'rb') as inF:
                arLibs |= pickle.load(inF)
        
        arCacheDir = os.path.dirname(arCache)
        if not os.path.isdir(arCacheDir) :
            try:
                os.makedirs(arCacheDir)
            except:
                pass
        try:
            with open(arCache, 'wb') as outp:
                pickle.dump(arLibs, outp, pickle.HIGHEST_PROTOCOL)
        except:
            if prDebug: sys.stderr.write ('Archive Access Error: '+ ar + '\n\n')
    for lib in arLibs:
        addFlags += ['-l'+lib]
    #print "addFlags: "+ str(addFlags)



    #for ar in archives:
        #arCache =  os.path.realpath(str(ar[:-2])+'.libs')
        #arCache = re.sub(r'/home/'+user+r'/workspace/','/home/'+user+r'/workspace/bcache/',arCache)
        ##print "AR: " + arCache
        #print "LIBS: " + str(libs)
        #arLibs = set(libs)
        #if os.path.isfile(arCache):
            #with open(arCache, 'rb') as inFile:
                #arLibs |= pickle.load(inFile)
        #with open(arCache, 'wb') as output:
            #pickle.dump(arLibs, output, pickle.HIGHEST_PROTOCOL)
        #print "AR LIBS: " + str(arLibs)
        

    #buildBin = [gccExec] + compilerFlags
    #buildBin = [clangExec, '-Xlinker', '-zmuldefs'] + addFlags+ compilerFlags
    buildBin = [clangExec, '-Xlinker', '-zmuldefs'] + compilerFlags
    #TODO try manual linking again
    #buildBin = ['gold'] + compilerFlags
    #buildBin = ['ld.gold'] + compilerFlags

    #TODO TIME THIS STEP
    if prDebug: sys.stderr.write (string.join(buildBin,' ')+'\n\n')
    return execBuild(buildBin, "Build Bin From Objs")
    


### BLOB FUNCTIONS ###

def cacheLineFlags(filename):
    obj = [None] * 5
    #obj = [None] * 6
    obj[0]=isAsm
    obj[1]=clangExec
    obj[2]=gccExec
    obj[3]=generateAssemblyCacheFlags
    obj[4]=assemblerFlags
    #obj[5]=includes
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def cacheBitcode(output, inFile=None):    # Build .bc file if there is no cached version
    global retCode
    if ( not os.path.isfile(output) ):        
        if prDebug: sys.stderr.write ("=== To Bitcode Cache ===" +'\n\n')
        #TODO CACHE INCLUDES
        #global includes
        #headers = set()
        #visited = set()
        #includes = set()
        #for sF in sources:
            #headers |= set([sF, re.sub(r'\.[cCsS]+[^o]?[pPxX+]*', r'.h', sF)])
            #while (len(headers) > 0):
                #print "HEADERS: "+str(headers)
                #header = headers.pop()
                #print "HEADER: "+str(header)
                #visited.add(header)
                #TODO FOR ALL DIR IN -I ...
                #headerFile=''
                #for folder in includeDir:
                    #print "HEADER: "+str(folder+'/'+header)
                    #if not os.path.isfile(folder+'/'+header):
                        #print "SKIPPING"
                        #continue
                    #else:
                        #headerFile = folder +'/'+header
                #if len(headerFile)==0:
                    #continue
                #print "PASS"
                #for line in open(headerFile):
                    #if "#include" in line:
                        #headers |= set(re.findall(r'["<](.*?)[>"]', line, re.I|re.DOTALL))
                        #headers = headers - visited
                        #incItem = re.findall(r'["<](.*?)\.\w+[>"]', line, re.I|re.DOTALL)
                        #includes |= set(incItem)
                        #print str(incItem)
        #if prDebug: sys.stderr.write ("INCLUDES: "+ str(includes)+'\n\n')
        cacheLineFlags(output[:-2]+'line')
        #print "====== CACHE BITCODE OUTPUT: " + output
        buildBc = ''
        if(inFile is None):
            if len(sources)!=0:
                #buildBc = [clangExec, '-o', output, '-S', '-emit-llvm'] + generateAssemblyFlags + sources
                buildBc = [clangExec, '-o', output, '-c', '-emit-llvm'] + generateAssemblyFlags + sources
        else:
            #buildBc = [clangExec, '-o', output, '-S', '-emit-llvm', inFile] + generateAssemblyFlags
            buildBc = [clangExec, '-o', output, '-c', '-emit-llvm', inFile] + generateAssemblyFlags
        
        if len(buildBc)==0:
            if prDebug: sys.stderr.write ('Build Nothing!?\n\n')
            return retCode

        if prDebug: sys.stderr.write (string.join(buildBc,' ')+'\n\n')
        return execBuild(buildBc,"To Bitcode Cache")
    if (Moverride and os.path.isfile(MCacheFile) ):
        if prDebug: sys.stderr.write ("=== -M Override ===" +'\n\n')
        cmd = ['cp', MCacheFile, MFile]
        #assemble = [gccExec, '-o', objFile, '-E'] + generateAssemblyFlags + sources #-E
        if prDebug: sys.stderr.write (string.join(cmd,' ')+'\n\n')
        if realBuild:
            process = subprocess.Popen(cmd)
            retCode = process.wait()
        return errorCatch(retCode, string.join(cmd,' '), 'Restore -M Output')
    return retCode

def linkAndCacheAssemblyBlob(output):
    global retCode
    if not os.path.isfile(output):
        if prDebug: sys.stderr.write ("=== Linking Bitcode Files ===" +'\n\n')

        inObj = [None] * len(objects)
        inSrc = [None] * len(sources)
        #inBC = set()

        
        #For each obj .o located cached .bc file
        for i,item in enumerate(objects):
            source = os.path.realpath(item)
            #if source[-3:] == '.so' or source[-3:] == '.SO' or bool(re.search(r'.[sS][oO][.0-9]*$',source)):
            #    pass
            #else:
            tempBC = re.sub(r'\.[ol][o]?$','.bc',source)
            inObj[i] = re.sub(r'/home/'+user+r'/workspace/','/home/'+user+r'/workspace/bcache/',tempBC)
        
        for i,item in enumerate(sources):
            source = os.path.realpath(item)
            tempBC = re.sub(r'\.[cC]+[pPxX+]*','.bc',source)
            inSrc[i] = re.sub(r'/home/'+user+r'/workspace/','/home/'+user+r'/workspace/bcache/',tempBC)
            #TODO FIXME
            cacheBitcode(inSrc[i], source)


        #TODO scan include statements
        #for file in sources, for line in file, if include then add to incSet

        #global generateAssemblyFlags
        #flags=[]
        #includes=set()
        #for filename in inObj:
        #    with open(filename[:-2]+'line', 'rb') as inFile:
        #        flags = pickle.load(inFile)
        #        includes |= set(flags[5])

        blobBc = output + ".bc"
        #llvmLink = ["llvm-link", "-S", "-o", blobBc] + inObj + inSrc + list(inBC)
        #llvmLink = ["llvm-link", "-o", blobBc] + inObj + inSrc + list(inBC)
        llvmLink = ["llvm-link", "-o", blobBc] + inObj + inSrc

        if prDebug: sys.stderr.write (string.join(llvmLink,' ')+'\n\n')
        retCode = execBuild(llvmLink, "Linking Bitcode Files") and retCode
        
        if retCode == 0:
            return cacheAssembly(output, blobBc);
    return retCode

def readLineFlags(filename):
    #global flags
    flags=None
    with open(filename, 'rb') as inFile:
        flags = pickle.load(inFile)
    #sys.stderr.write (str(flags))
    return flags

def buildBinFromBlobS(output, inFile):
    global retCode
    if retCode == 0:
        if prDebug: sys.stderr.write ("=== Build Bin From BlobS ===" +'\n\n')


        addFlags = []
        arLibs = set()
        for ar in archives:
            arCache = os.path.realpath(re.sub(r'\.[ahsS]+[oO]?','.libs',str(ar)))
            arCache = re.sub(r'/home/'+user+r'/workspace/','/home/'+user+r'/workspace/bcache/',arCache)
            #print "AR: " + arCache
            arLibs = set(libs)
            try:
                if os.path.isfile(arCache):
                    with open(arCache, 'rb') as inF:
                        arLibs |= pickle.load(inF)
                with open(arCache, 'wb') as outp:
                    pickle.dump(arLibs, outp, pickle.HIGHEST_PROTOCOL)
            except:
                if prDebug: sys.stderr.write ('Archive Access Error: '+ ar + '\n\n')
        for lib in arLibs:
            addFlags += ['-l'+lib]
        #print "addFlags: "+ str(addFlags)
        #TODO REMOVE HACK IMPLEMENTATION
        #if 'tar' in os.getcwd():
            #addFlags += ['-lrt']
        #if 'js' in os.getcwd():
        #    addFlags += ['-ljs']

        #TODO figure out how to build final bin
        #buildBin = ['as', "-o", output, inFile]
        if (output == 'a.out'):
            #buildBin = [clangExec, inFile] + blobCompilerFlags
            buildBin = [gccExec] + addFlags +[inFile, '-Xlinker', '-zmuldefs'] + blobCompilerFlags + archives
            #buildBin = [gccExec, inFile, '-Xlinker', '-zmuldefs'] + blobCompilerFlags + addFlags + archives
            #buildBin = [gccExec, inFile] + blobCompilerFlags + inArs
        else:
           ##buildBin = [clangExec] + blobCompilerFlags + ["-o", output, inFile]
            buildBin = [gccExec] + blobCompilerFlags + ["-o", output, inFile, '-Xlinker', '-zmuldefs']  + archives + addFlags
            #buildBin = [gccExec] + blobCompilerFlags + ["-o", output, inFile] 
            #buildBin = ['libtool', '--mode=link', gccExec] + blobCompilerFlags + ["-o", output, inFile, '-Xlinker', '-zmuldefs'] + addFlags
            #buildBin = [gccExec] + blobCompilerFlags + ["-o", output, inFile, '-Xlinker', '-zmuldefs'] + addFlags
            #buildBin = [gccExec] + blobCompilerFlags + ["-o", output, inFile, '-Xlinker', '-zmuldefs'] + addFlags + archives
            #buildBin = [gccExec] + blobCompilerFlags + ["-o", output, inFile] + inArs
            #buildBin = [gccExec, "-o", output, inFile] + blobCompilerFlags
        #buildBin = [gccExec, "-Wa,-alh,-L", "-o", output, inFile] + blobCompilerFlags
        #buildBin = [clangExec, "-o", output, inFile] + blobCompilerFlags

        #buildBin += extraFlags
        if prDebug: sys.stderr.write (string.join(buildBin,' ')+'\n\n')
        retCode = execBuild(buildBin, "Build Bin From BlobS") and retCode
        os.chmod(output, 0775)
        return retCode
    return retCode
    
### UTILITIES ###

def execBuild(cmd, mesg):
    global retCode
    if realBuild:
        if cmd[0] == clangExec or cmd[0] == gccExec:
            cmd += extraFlags
        process = subprocess.Popen(cmd)
        retCode = process.wait()
    return errorCatch(retCode, string.join(cmd,' '), mesg)
    
def failBuild():
    # Something didn't work. Fail back to compile from scratch.
    if prDebug: sys.stderr.write ("=== Fail Build Attempt ===" +'\n\n')
    return execBuild([gccExec] +  cmdLine.strip().split(), "Fail Build")
    #return execBuild([clangExec] +  cmdLine.strip().split(), "Fail Build")
    
def excludeBuild():
    # Something didn't work. Fail back to compile from scratch.
    if prDebug: sys.stderr.write ("=== Excluded Build Attempt ===" +'\n\n')
    if prDebug: sys.stderr.write (string.join([clangExec] + compilerFlags,' ')+'\n\n')
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
        sys.stderr.write( 'binFile: ' + binFile +'\n')
        sys.stderr.write( 'MFile: ' + MFile +'\n\n')
        
        sys.stderr.write( 'compilerFlags: ' + str(compilerFlags) +'\n\n')
        sys.stderr.write( 'generateAssemblyFlags: ' + str(generateAssemblyFlags) +'\n\n')
        sys.stderr.write( 'assemblerFlags: ' + str(assemblerFlags) +'\n\n')
        sys.stderr.write( 'blobCompilerFlags: ' + str(blobCompilerFlags) +'\n\n')
        sys.stderr.write( 'divannoFlags: ' + str(divannoFlags) +'\n\n')
        
        sys.stderr.write( 'sources: ' + str(sources) +'\n')
        sys.stderr.write( 'assemblys: ' + str(assemblys) +'\n')
        sys.stderr.write( 'objects: ' + str(objects) +'\n')
        sys.stderr.write( 'archives: ' + str(archives) +'\n\n')
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
    global generateAssemblyCacheFlags
    global divannoFlags
 
    global sources
    global assemblys
    global objects
    global archives
    global doBuildObj
    global doBuildBlob
    global doExcludeBuild
    global Moverride
    global MFile
    global MCacheFile
    global isAsm
    global seed
    global percent
    global includeDir
    includeDir = []
    global libs
    libs = []
    
    isOutput = False
    isParam = False
    isObjGen = False
    isPIC = False
    isObjBuild = False
    doGrabInc = False
    doGrabLib = False

    for var in varList:
        #Final compile must be ordered specifically

        #-Qunused-arguments caused problems and is therefore ...unused...
        if var == '-Qunused-arguments':
            continue


        compilerFlags += [var]

        if isOutput:
            #if var in mustBuildObj:
            #    doBuildObj = True

            if var[-2:] == '.o':
                objFile = var
                rawFile = var[:-2]
            elif var[-3:] == '.lo':
                objFile = var
                rawFile = var[:-3]
            elif var[-3:] == '.so' or var[-3:] == '.la':
                binFile = var
                rawFile = var[:-3]
            else:
                binFile = var
                rawFile = var
                
            isOutput = False
            continue
        
        if isParam:
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
            isParam=False
            continue

        if isObjGen:
            isObjGen=False
            if var == '-MF' or var == '-MT' or var == '-MQ':
                #assemblerFlags += [var]
                #blobCompilerFlags += [var]
                generateAssemblyFlags += [var]
                isObjGen=True
                continue
            #assemblerFlags += [var]
            #blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            MFile = var
            continue
                
        if doGrabLib:
            libs += [var]
            blobCompilerFlags += [var]
            assemblerFlags += [var]
            doGrabLib=False
            continue

        if doGrabInc:
            includeDir += [var]
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
            doGrabInc=False
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
        elif (var[:14] == '-frandom-seed='):
            seed = var[14:]
        elif (var[:26] == '-nop-insertion-percentage='):
            percent = var[26:]
        elif (var == '-nop-insertion' or var == "-mov-to-lea" or var == "-sched-randomize"):
            divannoFlags += [var]
        elif (var == '-Xclang' or var == "-mllvm"):
            continue #TODO Do something with these eventually.....
        elif (var[:16] == '-print-prog-name'
            or var == '-print-search-dirs'
            or var == '-print-multi-os-directory'):
            doExcludeBuild = True
        elif (var == '-v' or var == '-V' 
            or var == '--version' 
            or var == '-qversion' 
            or var == '-dumpversion'):
            doExcludeBuild = True
        elif var == '--param':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
            isParam = True
        elif var == '-include':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
            doGrabInc = True
        elif var == '-M' or var == '-MM' or var == '-MD' or var == '-MMD' or  var == '-MP' or var == '-MG':
            Moverride=True
            #assemblerFlags += [var]
            #blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
        elif var == '-MF' or var == '-MT' or var == '-MQ':
            #TODO MULTIPLE FILES
            Moverride=True
            #assemblerFlags += [var]
            #blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            isObjGen = True
        elif (var == '-rpath'):
            ###blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
            isObjGen = True
        elif (var == '-pthread'):
            assemblerFlags += [var]
            blobCompilerFlags += [var]
        elif (var == '-avoid-version'):# or var == '-module'):
            assemblerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
        elif (var[:4] == '-std'
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
            generateAssemblyCacheFlags += [var]
        elif var == '-fPIC' or var == '-DPIC':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
            isPIC = True
        elif var[:2] == '-L':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
        elif var[:2] == '-D' or var[:2] == '-U':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
        elif var[:2] == '-O':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
        elif var[:2] == '-I':
            if len(var)==2:doGrabInc=True
            blobCompilerFlags += [var]
            includeDir += [var[2:]]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
        elif var[:3] == '-Wp':
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
        elif var[:3] == '-Wa':
            blobCompilerFlags += [var]
            assemblerFlags +=[var]
        elif var[:3] == '-Wl':
            blobCompilerFlags += [var]
            assemblerFlags +=[var]
        elif var[:2] == '-W':
            addFlagsAll(var)
        elif var[:2] == '-f':
            blobCompilerFlags += [var]
            generateAssemblyFlags += [var]
            generateAssemblyCacheFlags += [var]
        elif var[:2] == '-l':
            #compilerFlags = ['-L/usr/local/lib', '-L/lib/x86_64-linux-gnu', '-L/usr/lib/x86_64-linux-gnu'] + compilerFlags
            if len(var)==2:doGrabLib=True
            else:libs+=[var[2:]]
            blobCompilerFlags += [var]
            assemblerFlags += [var]
        elif var == '-o':
            isOutput = True
            continue
        elif var == '-c':
            isObjBuild = True
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
            isAsm = True
            #TODO preprocess .S
            sources += [var]
        elif (var[-3:] == '.pp' or var[-3:] == '.PP'):
            #FIREFOX
            blobCompilerFlags += [var]
        elif (var[-2:] == '.a' or var[-2:] == '.h'):
            archives += [var]
        elif (var[-2:] == '.s'):
            #TODO Can there ever be more than one source?
            assemblys += [var]
        elif (var[-3:] == '.so' or var[-3:] == '.SO' or bool(re.search(r'.[sS][oO][.0-9]*$',var))):
            archives += [var]
        elif (var[-2:] == '.o' or var[-2:] == '.O' or var[-3:] == '.lo'):
            objects += [var]
        else:
            #addFlagsAll(var)
            errorCatch(1,var,'initVars')
    
    
        # TODO make portable; raw compile configure
#    if (
#         or bool(re.search(r'\sconftest\.[ocC]?\s',cmdLine)) #conf exempt
#         or bool(re.search(r'/config/?',os.getcwd())) #config folder exempt
#       ):
    
    #Not sure if needed
    #generateAssemblyFlags += ['-fPIC']
    #compilerFlags += ['-fPIC']
    
    #not = bin?
    if isObjBuild and len(objFile)==0 and len(sources)==1 :
        objFile = os.getcwd() +'/'+ re.sub(r'\.[cCsS]+[^o]?[pPxX+]*','.o',os.path.basename(sources[0]) )
        #print objFile
        rawFile = objFile[:-2]
    
    if len(binFile)==0 and len(objFile)==0 :
        binFile = 'a.out'
    
    rawFile = os.path.realpath(rawFile)
    cachedFile = re.sub(r'/home/'+user+r'/workspace/','/home/'+user+r'/workspace/bcache/',rawFile)
    MCacheFile = re.sub(r'/home/'+user+r'/workspace/','/home/'+user+r'/workspace/bcache/',os.path.realpath(MFile))

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
                
    McacheDir = os.path.dirname(MCacheFile)
    if McacheDir != '':
        if not os.path.isdir(McacheDir) :
            if mkdirFlag :
                try:
                    os.makedirs(McacheDir)
                except:
                    pass
            else:
                sys.stderr.write ('mkdir file\'s dir: '+McacheDir +'\n')
    
    #Copy assembly files now to save time later
    for item in assemblys:
        asmFile = os.path.realpath(item)
        cmd = ['cp', item, cachedFile+'.s' ]
        if realBuild:
            process = subprocess.Popen(cmd)
            retCode = process.wait()
        isAsm = True
        return errorCatch(retCode, string.join(cmd,' '), 'Copy Existing Assembly')
    #DEBUG
    #errorCatch(1,'Testing initVars','initVars')
    #Moverride=False
    
    
def addFlagsAll(flag):
    global blobCompilerFlags
    global assemblerFlags
    global generateAssemblyFlags
    global generateAssemblyCacheFlags
    blobCompilerFlags += [flag]
    assemblerFlags += [flag]
    generateAssemblyFlags += [flag]
    generateAssemblyCacheFlags += [flag]
    

if __name__ == "__main__":
    main()
