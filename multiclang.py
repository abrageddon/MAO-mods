#!/usr/bin/python
import sys, os, re, string, subprocess, shutil, random, getpass, pickle, time

# output to std err
#prDebug=True
prDebug=False
# really make dirs, not just print
mkdirFlag=True 
# really build, not just print
realBuild=True

doBuildObj=True ; doBuildBlob=False
#doBuildObj=False ; doBuildBlob=True
#doBuildObj=True ; doBuildBlob=True

extraFlags = []
#extraFlags = ['-time', '-ftime-report'] ; prDebug=True


idStr="-Wl,--build-id=0xDECAFBAD"

clangExec = '/mnt/multicompiler/build/Release+Asserts/bin/clang'
gccExec = 'gcc'
retCode = 0
doExcludeBuild = False
Moverride = False
isAsm = False

compilerFlags = []
blobCompilerFlags = []
assemblerFlags = []
generateBitcodeFlags = []
compileBitcodeFlags = []
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
#prefix = '/home/'+user
prefix = '/mnt'

def main():
    global timeTest
    timeTest = time.time()

    global retCode

    
    
    #TODO pull seed and percent from commandline 
    # Pick the correct clang....
    if ('++' in sys.argv[0]):
        global clangExec
        global gccExec
        clangExec = '/mnt/multicompiler/build/Release+Asserts/bin/clang++'
        gccExec = 'g++'
    
    global cmdLine
    cmdLine = ' ' + string.join(sys.argv[1:],' ') + ' '
    #print cmdLine

    initVars(sys.argv[1:])


    # TODO make portable; raw compile configure
    if ( doExcludeBuild
         or bool(re.search(r'conftest\.?[ocC]*\s?',cmdLine)) #conf exempt
         or bool(re.search(r'/config/?',os.getcwd())) #FIREFOX
         or bool(re.search(r'workspace/[^/]+/[^/]+\Z',os.getcwd())) #FIREFOX
        ):excludeBuild()

    

    # name cached file
    #TODO REMOVE THESE 
    global bcFile
    global asmFile
    global annotatedAsmFile
    global blobS
    global blobBc
    global blobSDiv
    global blobLabel
    global annotatedAsmBlobFile
    bcFile = cachedFile + ".bc"
    asmFile = cachedFile + ".s"
    labeledBc = cachedFile + ".label.bc"
    annotatedAsmFile = cachedFile + ".a.s"
    blobS = cachedFile + ".blob.s"
    blobBc = cachedFile + ".blob.bc"
    blobSDiv = cachedFile + ".blob.div.s"
    blobLabel = cachedFile + ".blob.label.bc"
    annotatedAsmBlobFile = cachedFile + ".blob.a.s"


    
    #print "TIME TO INIT: "+ str(time.time() - timeTest)
    # There is an .o output file we want to cache
    if len(objFile)!=0:
        # determine location of cached bitcode
        #cacheBitcode(bcFile)#TEMP

        if len(assemblys)!=0 and len(sources)==0:
            buildObjFromASM(objFile, assemblys[0])
        else:
            cacheBitcode(bcFile)

            labelOpt(labeledBc, bcFile)
            #buildObjFromBc(objFile, bcFile)

            buildObjFromBc(objFile, labeledBc)
    
    if  len(binFile)!=0:

        #TODO if compiling from .c to bin, do different build
        
        #if input is .c and input.bc doesn't exist; build input.c bitcode
        #if blob doesnt exist; use input.c as .bc

        #TODO CORRECT THIS PART FOR DIVANNO
        buildBinFromObjs()
        

    if len(objFile) == 0 and len(binFile) == 0:
        errorCatch(1,'No Output File','')

    if prDebug: sys.stderr.write( "MAOclang RUNTIME: "+ str(time.time() - timeTest) +'\n')
    if prDebug: sys.stderr.write( "\n" )
    sys.exit(retCode)


### FUNCTIONS ###

def labelOpt(output, inFile):
    if prDebug: sys.stderr.write ("=== LabelAll Opt ===" +'\n\n')
    if os.path.isfile(output):
        if prDebug: sys.stderr.write (output +'\n\n')
        return retCode
    labelAll = ["-load", "/mnt/multicompiler/build/Release+Asserts/lib/LabelAll.so", "-labelall"]

    label = ["opt", "-o", output, inFile ] + labelAll

    if prDebug: sys.stderr.write (string.join(label,' ')+'\n\n')
    return execBuild(label, "LabelAll Opt")

def buildObjFromBc(output, inFile):
    if prDebug: sys.stderr.write ("=== BC To Obj ===" +'\n\n')

    buildObj = [clangExec, '-o', output, '-c'] + compileBitcodeFlags + [inFile] + [idStr]

    if prDebug: sys.stderr.write (string.join(buildObj,' ')+'\n\n')
    return execBuild(buildObj,"BC To Obj")

def buildBinFromObjs():
    if prDebug: sys.stderr.write ("=== Build Bin From Objs ===" +'\n\n')

    buildBin = [clangExec] + compilerFlags + [idStr]

    if prDebug: sys.stderr.write (string.join(buildBin,' ')+'\n\n')
    return execBuild(buildBin, "Build Bin From Objs")
    
def buildObjFromASM(output, inFile):
    if prDebug: sys.stderr.write ("=== ASM To Obj ===" +'\n\n')

    buildBin = [clangExec] + compilerFlags + [idStr]

    if prDebug: sys.stderr.write (string.join(buildObj,' ')+'\n\n')
    return execBuild(buildBin,"ASM To Obj")

### BLOB FUNCTIONS ###
def cacheBitcode(output, inFile=None):    # Build .bc file if there is no cached version
    #if prDebug: sys.stderr.write ("=== Bitcode Cache ===" + output +'\n\n')
    global retCode
    if ( True or not os.path.isfile(output) ):        
        if prDebug: sys.stderr.write ("=== To Bitcode Cache ===" +'\n\n')
        buildBc = ''
        if(inFile is None):
            if len(sources)!=0:
                buildBc = [clangExec, '-o', output, '-S', '-emit-llvm'] + generateBitcodeFlags + sources
        else:
            buildBc = [clangExec, '-o', output, '-S', '-emit-llvm', inFile] + generateBitcodeFlags
        
        if len(buildBc)==0:
            if prDebug: sys.stderr.write ('Build Nothing!?\n\n')
            retCode = 1
            return retCode

        if prDebug: sys.stderr.write (string.join(buildBc,' ')+'\n\n')
        return execBuild(buildBc,"To Bitcode Cache")
    else:
        if prDebug: sys.stderr.write ("=== Use Bitcode Cache ===\n\n" + output +'\n\n')
    if (False and Moverride and os.path.isfile(MCacheFile) ):
        if prDebug: sys.stderr.write ("=== -M Override ===" +'\n\n')
        cmd = ['cp', MCacheFile, MFile]
        #assemble = [gccExec, '-o', objFile, '-E'] + generateAssemblyFlags + sources #-E
        if prDebug: sys.stderr.write (string.join(cmd,' ')+'\n\n')
        if realBuild:
            process = subprocess.Popen(cmd)
            retCode = process.wait()
        return errorCatch(retCode, string.join(cmd,' '), 'Restore -M Output')
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
    return execBuild([clangExec] +  cmdLine.strip().split(), "Fail Build")
    
def excludeBuild():
    # Something didn't work. Fail back to compile from scratch.
    if prDebug: sys.stderr.write ("=== Excluded Build Attempt ===" +'\n\n')
    if prDebug: sys.stderr.write (string.join([clangExec] + compilerFlags + [idStr],' ')+'\n\n')
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
        sys.stderr.write( 'generateBitcodeFlags: ' + str(generateBitcodeFlags) +'\n\n')
        sys.stderr.write( 'compileBitcodeFlags: ' + str(compileBitcodeFlags) +'\n\n')
        
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
    global generateBitcodeFlags
    global compileBitcodeFlags
 
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
    isXclang = False
    ismllvm = False

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
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
            isParam=False
            continue

        if isObjGen:
            isObjGen=False
            if var == '-MF' or var == '-MT' or var == '-MQ':
                generateBitcodeFlags += [var]
                #compileBitcodeFlags += [var]
                isObjGen=True
                continue
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
            MFile = var
            continue
                
        if doGrabLib:
            libs += [var]
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
            doGrabLib=False
            continue

        if doGrabInc:
            includeDir += [var]
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
            doGrabInc=False
            continue
        # Exclude from genAssembly     -D_FORTIFY_SOURCE=1

        if isXclang:
            if var != "-nop-insertion":
                generateBitcodeFlags += ["-Xclang", var]
            compileBitcodeFlags += ["-Xclang", var]
            isXclang = False
            continue

        if ismllvm:
            if (  var != "-shuffle-stack-frames"
              and var != "-sched-randomize"
              and var != "-randomize-registers"
              and var != "-randomize-function-list"
              and var != "-profiled-nop-insertion"
              and var != "-profile-info-file"
              and var != "-nop-insertion-range"
              and var != "-nop-insertion-use-log"
              and var != "-use-function-options"
              and var != "-function-options-file"
              and var[:19] != "-max-stack-pad-size"
              and var[:24] != "-pre-RA-randomizer-range"
              and var[:27] != "-sched-randomize-percentage"
              and var[:25] != "-nop-insertion-percentage"
              and var[:25] != "-max-nops-per-instruction"
              and var[:22] != "-mov-to-lea-percentage"
              and var[:16] != "-align-functions"
              and var[:9] != "-rng-seed" ) :
                generateBitcodeFlags += ["-mllvm", var]
            compileBitcodeFlags += ["-mllvm", var]
            ismllvm = False
            continue

#TODO add seed, percent, debug flags to be read from commandline    
#    if (sys.argv[1] == "-prDebug"):prDebug = True


        if var == '':
            continue
        #FLAGS
        elif var == '-E':
            doExcludeBuild = True
        elif var == '-S':
            doExcludeBuild = True
        elif (var[:14] == '-frandom-seed=' or var == "-fdiversify"):
            compileBitcodeFlags += [var]
        elif (var == '-Xclang'):
            isXclang = True
            continue 
        elif (var == "-mllvm"):
            ismllvm = True
            continue 
        #elif (var[:26] == '-nop-insertion-percentage='):
            #percent = var[26:]
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
            isParam = True
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
        elif var == '-M' or var == '-MM' or var == '-MD' or var == '-MMD' or  var == '-MP' or var == '-MG':
            Moverride=True
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
        elif var == '-MF' or var == '-MT' or var == '-MQ':
            #TODO MULTIPLE FILES
            Moverride=True
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
            isObjGen = True
        elif (var == '-rpath'):
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
            isObjGen = True
        elif (var == '-pthread'):
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif (var == '-avoid-version'):# or var == '-module'):
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
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
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif var == '-fPIC' or var == '-DPIC':
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
            isPIC = True
        elif var[:2] == '-L':
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif var[:2] == '-D' or var[:2] == '-U':
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
        elif var[:2] == '-O':
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
        elif var[:2] == '-I':
            if len(var)==2:doGrabInc=True
            includeDir += [var[2:]]
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
        elif var == '-include':
            generateBitcodeFlags += [var]
            #compileBitcodeFlags += [var]
            doGrabInc = True
        elif var[:3] == '-Wp':
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif var[:3] == '-Wa':
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif var[:3] == '-Wl':
            #generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif var[:2] == '-W':
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif var[:2] == '-f':
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif var[:2] == '-l':
            if len(var)==2:doGrabLib=True
            else:libs+=[var[2:]]
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        elif var == '-o':
            isOutput = True
            continue
        elif var == '-c':
            isObjBuild = True
        elif var[:1] == '-':
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
        #FILES    
        elif (var[-2:] == '.c' or var[-2:] == '.C' 
            or var[-3:] == '.cc' or var[-3:] == '.CC' 
            or var[-4:] == '.cpp' or var[-4:] == '.cpp' 
            or var[-4:] == '.CPP' or var[-4:] == '.CPP' 
            or var[-4:] == '.cxx' or var[-4:] == '.cxx' 
            or var[-4:] == '.CXX' or var[-4:] == '.CXX'):
            sources += [var]
        elif (var[-2:] == '.S'):
            #isAsm = True
            #TODO preprocess .S
            assemblys += [var]
        elif (var[-3:] == '.pp' or var[-3:] == '.PP'):
            #FIREFOX
            generateBitcodeFlags += [var]
            compileBitcodeFlags += [var]
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
    cachedFile = re.sub(prefix+r'/workspace/',prefix+r'/workspace/bcache/',rawFile)
    MCacheFile = re.sub(prefix+r'/workspace/',prefix+r'/workspace/bcache/',os.path.realpath(MFile))

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
    
    

if __name__ == "__main__":
    main()
