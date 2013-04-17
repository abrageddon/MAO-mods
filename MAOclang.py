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

    doBuildObj=False
    doBuildBlob=True
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
                diversify(asmFile+"Div.s", asmFile)
            else:
                diversifyClang(asmFile+"Div.s", bcFile)

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
    
    #FIREFOX
    buildFromObjList = ["libnspr4.so", "libmozalloc.so", "host_jskwgen", "host_jsoplengen"]
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
	, "mozalloc.o", "mozalloc_abort.o", "mozalloc_oom.o", "plarena.o", "plhash.o"
	, "plvrsion.o", "strlen.o", "strcpy.o", "strdup.o", "strcase.o", "strcat.o"
	, "strcmp.o", "strchr.o", "strpbrk.o", "strstr.o", "strtok.o", "base64.o"
	, "plerror.o", "plgetopt.o", "libffi.a", "debug.o", "prep_cif.o", "types.o"
	, "raw_api.o", "java_raw_api.o", "closures.o", "ffi64.o", "unix64.o", "ffi.o"
        , "sysv.o", "host_jskwgen.o", "host_jsoplengen.o", "jsalloc.o", "jsanalyze.o"
	, "jsapi.o", "jsarray.o", "jsatom.o", "jsbool.o", "jsclone.o", "jscntxt.o"
	, "jscompartment.o", "jsdate.o", "jsdbgapi.o", "jsdhash.o", "jsdtoa.o"
	, "jsexn.o", "jsfriendapi.o", "jsfun.o", "jsgc.o", "jscrashreport.o"
	, "jshash.o", "jsinfer.o", "jsinterp.o", "jsiter.o", "jslog2.o", "jsmath.o"
	, "jsnativestack.o", "jsnum.o", "jsobj.o", "json.o", "jsonparser.o"
	, "jsopcode.o", "jsproxy.o", "jsprf.o", "jsprobes.o", "jspropertycache.o"
	, "jspropertytree.o", "jsreflect.o", "jsscope.o", "jsscript.o", "jsstr.o"
	, "jstypedarray.o", "jsutil.o", "jswatchpoint.o", "jsweakmap.o"
	, "jswrapper.o", "jsxml.o", "prmjtime.o", "sharkctl.o", "ArgumentsObject.o"
	, "ScopeObject.o", "Debugger.o", "GlobalObject.o", "ObjectImpl.o", "Stack.o"
	, "String.o", "BytecodeCompiler.o", "BytecodeEmitter.o", "FoldConstants.o"
	, "ParseMaps.o", "ParseNode.o", "Parser.o", "SemanticAnalysis.o"
	, "SPSProfiler.o", "TokenStream.o", "TreeContext.o", "TestingFunctions.o"
	, "LifoAlloc.o", "Eval.o", "MapObject.o", "MemoryMetrics.o", "RegExpObject.o"
	, "RegExpStatics.o", "RegExp.o", "Marking.o", "Memory.o", "Statistics.o"
	, "StoreBuffer.o", "StringBuffer.o", "Unicode.o", "Xdr.o", "MethodJIT.o"
	, "StubCalls.o", "Compiler.o", "FrameState.o", "FastArithmetic.o"
	, "FastBuiltins.o", "FastOps.o", "LoopState.o", "StubCompiler.o", "MonoIC.o"
	, "PolyIC.o", "ImmutableSync.o", "InvokeHelpers.o", "Retcon.o"
	, "TrampolineCompiler.o", "ExecutableAllocator.o", "PageBlock.o"
	, "YarrInterpreter.o", "YarrPattern.o", "YarrSyntaxChecker.o"
	, "ExecutableAllocatorPosix.o", "OSAllocatorPosix.o", "ARMAssembler.o"
	, "MacroAssemblerARM.o", "MacroAssemblerX86Common.o", "YarrJIT.o", "CTypes.o"
	, "Library.o", "jsperf.o", "pm_linux.o", "editline.o", "sysunix.o"
	, "xpt_arena.o", "xpt_struct.o", "xpt_xdr.o", "nsDependentString.o"
	, "nsDependentSubstring.o", "nsPromiseFlatString.o", "nsReadableUtils.o"
	, "nsSubstring.o", "nsSubstringTuple.o", "nsString.o", "nsStringComparator.o"
	, "nsStringObsolete.o", "nsUTF8UtilsSSE2.o", "AppData.o"
	, "nsArrayEnumerator.o", "nsArrayUtils.o", "nsCategoryCache.o"
	, "nsCOMPtr.o", "nsCOMArray.o", "nsCRTGlue.o", "nsClassInfoImpl.o"
	, "nsComponentManagerUtils.o", "nsEnumeratorUtils.o", "nsID.o"
	, "nsIInterfaceRequestorUtils.o", "nsINIParser.o", "nsISupportsImpl.o"
	, "nsMemory.o", "nsWeakReference.o", "nsVersionComparator.o"
	, "nsTHashtable.o", "nsQuickSort.o", "nsVoidArray.o", "nsTArray.o"
	, "nsThreadUtils.o", "nsTObserverArray.o", "nsCycleCollectionParticipant.o"
	, "nsCycleCollectorUtils.o", "nsDeque.o", "pldhash.o", "BlockingResourceBase.o"
	, "DeadlockDetector.o", "SSE.o", "unused.o", "nsProxyRelease.o"
	, "nsTextFormatter.o", "GenericFactory.o", "FileUtils.o", "nsStringAPI.o"
	, "GenericModule.o", "AppData.o", "nsArrayEnumerator.o", "nsArrayUtils.o"
	, "nsCategoryCache.o", "nsCOMPtr.o", "nsCOMArray.o", "nsCRTGlue.o"
	, "nsClassInfoImpl.o", "nsComponentManagerUtils.o", "nsEnumeratorUtils.o"
	, "nsID.o", "nsIInterfaceRequestorUtils.o", "nsINIParser.o", "nsISupportsImpl.o"
	, "nsMemory.o", "nsWeakReference.o", "nsVersionComparator.o", "nsTHashtable.o"
	, "nsQuickSort.o", "nsVoidArray.o", "nsTArray.o", "nsThreadUtils.o"
	, "nsTObserverArray.o", "nsCycleCollectionParticipant.o"
	, "nsCycleCollectorUtils.o", "nsDeque.o", "pldhash.o", "nsStringAPI.o"
	, "nsXPCOMGlue.o", "nsGlueLinkingDlopen.o", "nsVersionComparatorImpl.o"
	, "nsConsoleMessage.o", "nsConsoleService.o", "nsDebugImpl.o", "nsErrorService.o"
	, "nsExceptionService.o", "nsMemoryImpl.o", "nsTraceRefcntImpl.o"
	, "nsInterfaceRequestorAgg.o", "nsUUIDGenerator.o", "nsSystemInfo.o"
	, "nsCycleCollector.o", "nsStackWalk.o", "nsMemoryReporterManager.o"
	, "FunctionTimer.o", "ClearOnShutdown.o", "VisualEventTracer.o"
	, "MapsMemoryReporter.o", "nsArray.o", "nsAtomTable.o", "nsAtomService.o"
	, "nsByteBuffer.o", "nsCRT.o", "nsFixedSizeAllocator.o", "nsHashPropertyBag.o"
	, "nsHashtable.o", "nsINIParserImpl.o", "nsObserverList.o", "nsObserverService.o"
	, "nsProperties.o", "nsPersistentProperties.o", "nsStaticNameTable.o"
	, "nsStringEnumerator.o", "nsSupportsArray.o", "nsSupportsArrayEnumerator.o"
	, "nsSupportsPrimitives.o", "nsUnicharBuffer.o", "nsVariant.o", "TimeStamp_posix.o"
	, "Base64.o", "nsAppFileLocationProvider.o", "nsBinaryStream.o", "nsDirectoryService.o"
	, "nsEscape.o", "nsInputStreamTee.o", "nsLinebreakConverter.o", "nsLocalFileCommon.o"
	, "nsMultiplexInputStream.o", "nsNativeCharsetUtils.o", "nsPipe3.o", "nsStreamUtils.o"
	, "nsScriptableInputStream.o", "nsScriptableBase64Encoder.o", "nsSegmentedBuffer.o"
	, "nsStorageStream.o", "nsStringStream.o", "nsUnicharInputStream.o", "nsIOUtil.o"
	, "nsWildCard.o", "SpecialSystemDirectory.o", "nsLocalFileUnix.o", "nsCategoryManager.o"
	, "nsComponentManager.o", "ManifestParser.o", "nsNativeComponentLoader.o"
	, "nsEventQueue.o", "nsEnvironment.o", "nsThread.o", "nsThreadManager.o"
	, "nsThreadPool.o", "nsProcessCommon.o", "nsTimerImpl.o", "TimerThread.o"
	, "HangMonitor.o", "LazyIdleThread.o", "xptiInterfaceInfo.o"
	, "xptiInterfaceInfoManager.o", "xptiTypelibGuts.o", "xptiWorkingSet.o"
	, "xptcall.o", "nsChromeRegistry.o", "nsChromeRegistryChrome.o"
	, "nsChromeProtocolHandler.o", "nsChromeRegistryContent.o", "AppData.o"
	, "nsArrayEnumerator.o", "nsArrayUtils.o", "nsCategoryCache.o", "nsCOMPtr.o"
	, "nsCOMArray.o", "nsCRTGlue.o", "nsClassInfoImpl.o", "nsComponentManagerUtils.o"
	, "nsEnumeratorUtils.o", "nsID.o", "nsIInterfaceRequestorUtils.o", "nsINIParser.o"
	, "nsISupportsImpl.o", "nsMemory.o", "nsWeakReference.o", "nsVersionComparator.o"
	, "nsTHashtable.o", "nsQuickSort.o", "nsVoidArray.o", "nsTArray.o", "nsThreadUtils.o"
	, "nsTObserverArray.o", "nsCycleCollectionParticipant.o", "nsCycleCollectorUtils.o"
	, "nsDeque.o", "pldhash.o", "BlockingResourceBase.o", "DeadlockDetector.o", "SSE.o"
	, "unused.o", "nsProxyRelease.o", "nsTextFormatter.o", "GenericFactory.o", "FileUtils.o"
	, "nsXPComInit.o", "nsXPCOMStrings.o", "Services.o", "Omnijar.o", "FileLocation.o"
	, "mozPoisonWriteStub.o", "nsPrefBranch.o", "nsPrefsFactory.o", "prefapi.o", "prefread.o"
	, "Preferences.o", "hyphen.o", "nsHyphenator.o", "nsHyphenationManager.o", "hnjstdio.o"
        , "nsCollation.o", "nsScriptableDateFormat.o", "nsLanguageAtomService.o", "nsLocale.o"
	, "nsLocaleService.o", "nsCharsetAlias.o", "nsUConvPropertySearch.o", "nsCollationUnix.o"
	, "nsDateTimeFormatUnix.o", "nsPosixLocale.o", "nsUNIXCharset.o", "nsJISx4501LineBreaker.o"
	, "nsSampleWordBreaker.o", "nsSemanticUnitScanner.o", "nsPangoBreaker.o", "nsStringBundle.o"
	, "nsStringBundleTextOverride.o", "nsUnicharUtils.o", "nsBidiUtils.o", "nsSpecialCasingData.o"
	, "nsUnicodeProperties.o", "nsCaseConversionImp2.o", "nsCategoryImp.o", "nsEntityConverter.o"
	, "nsSaveAsCharset.o", "nsUnicodeNormalizer.o", "ugen.o", "uscan.o", "umap.o", "nsUCSupport.o"
	, "nsUCConstructors.o", "nsUnicodeDecodeHelper.o", "nsUnicodeEncodeHelper.o"
	, "nsJapaneseToUnicode.o", "nsUnicodeToSJIS.o", "nsUnicodeToEUCJP.o", "nsUnicodeToISO2022JP.o"
	, "nsUnicodeToJISx0201.o", "nsGB2312ToUnicodeV2.o", "nsUnicodeToGB2312V2.o", "nsGBKToUnicode.o"
	, "nsUnicodeToGBK.o", "nsISO2022CNToUnicode.o", "nsUnicodeToISO2022CN.o", "nsHZToUnicode.o"
	, "nsUnicodeToHZ.o", "nsGBKConvUtil.o"
        ]
    buildDirs = ["/uconv/" # TODO checkthese requirements
        ## FIRFOX AR dirs
        #, "/build/unix/stdc++compat"
        #, "/memory/build"
        #, "/mozglue/build"
        #, "/nsprpub/pr/src"
        #, "/nsprpub/lib/ds"
        #, "/nsprpub/lib/libc/src"
        #, "/js/src/ctypes/libffi"
        ###, "/js/src/tmp4xq13P"
        ###, "/js/src"
        #, "/xpcom/typelib/xpt/src"
        #, "/xpcom/glue"
        #, "/xpcom/glue/standalone"
        #, "/xpcom/glue/nomozalloc"
        #, "/intl/unicharutil/util"
        #, "/intl/unicharutil/util/internal"
        #, "/modules/libbz2/src"
        #, "/rdf/util/src"
        #, "/modules/libmar/src"
        #, "/toolkit/crashreporter/google-breakpad/src/common"
        #, "/toolkit/crashreporter/google-breakpad/src/common/dwarf"
        #, "/toolkit/crashreporter/google-breakpad/src/common/linux"

	## FIREFOX pythonPath most of these require objects to be made
        , "accessible/build"
        , "accessible/public"
        , "accessible/src/atk"
        , "accessible/src/base"
        , "accessible/src/generic"
        , "accessible/src/html"
        , "accessible/src/xpcom"
        , "accessible/src/xul"
        , "browser/app"
        , "browser/components"
        , "browser/components/about"
        , "browser/components/build"
        , "browser/components/dirprovider"
        , "browser/components/feeds/public"
        , "browser/components/feeds/src"
        , "browser/components/migration/public"
        , "browser/components/migration/src"
        , "browser/components/privatebrowsing/src"
        , "browser/components/sessionstore"
        , "browser/components/shell/public"
        , "browser/components/shell/src"
        , "browser/fuel/public"
        , "build/unix/stdc++compat"
        , "caps/idl"
        , "caps/src"
        , "chrome/public"
        , "chrome/src"
        , "content/base/public"
        , "content/base/src"
        , "content/canvas/public"
        , "content/canvas/src"
        , "content/events/public"
        , "content/events/src"
        , "content/html/content/public"
        , "content/html/content/src"
        , "content/html/document/public"
        , "content/html/document/src"
        , "content/mathml/content/src"
        , "content/media"
        , "content/media/dash"
        , "content/media/ogg"
        , "content/media/raw"
        , "content/media/wave"
        , "content/media/webaudio"
        , "content/media/webm"
        , "content/media/webrtc"
        , "content/smil"
        , "content/svg/content/src"
        , "content/svg/document/src"
        , "content/xbl/src"
        , "content/xml/content/src"
        , "content/xml/document/src"
        , "content/xslt/public"
        , "content/xslt/src/base"
        , "content/xslt/src/xml"
        , "content/xslt/src/xpath"
        , "content/xslt/src/xslt"
        , "content/xul/content/public"
        , "content/xul/content/src"
        , "content/xul/document/public"
        , "content/xul/document/src"
        , "content/xul/templates/public"
        , "content/xul/templates/src"
        , "db/sqlite3/src"
        , "docshell/base"
        , "docshell/build"
        , "docshell/shistory/public"
        , "docshell/shistory/src"
        , "dom/activities/interfaces"
        , "dom/activities/src"
        , "dom/alarm"
        , "dom/audiochannel"
        , "dom/base"
        , "dom/battery"
        , "dom/bindings"
        , "dom/browser-element"
        , "dom/camera"
        , "dom/contacts"
        , "dom/devicestorage"
        , "dom/encoding"
        , "dom/file"
        , "dom/indexedDB"
        , "dom/indexedDB/ipc"
        , "dom/interfaces/apps"
        , "dom/interfaces/base"
        , "dom/interfaces/canvas"
        , "dom/interfaces/contacts"
        , "dom/interfaces/core"
        , "dom/interfaces/css"
        , "dom/interfaces/devicestorage"
        , "dom/interfaces/events"
        , "dom/interfaces/geolocation"
        , "dom/interfaces/html"
        , "dom/interfaces/json"
        , "dom/interfaces/load-save"
        , "dom/interfaces/notification"
        , "dom/interfaces/offline"
        , "dom/interfaces/permission"
        , "dom/interfaces/range"
        , "dom/interfaces/settings"
        , "dom/interfaces/sidebar"
        , "dom/interfaces/smil"
        , "dom/interfaces/storage"
        , "dom/interfaces/stylesheets"
        , "dom/interfaces/svg"
        , "dom/interfaces/traversal"
        , "dom/interfaces/xbl"
        , "dom/interfaces/xpath"
        , "dom/interfaces/xul"
        , "dom/ipc"
        , "dom/media"
        , "dom/media/bridge"
        , "dom/messages/interfaces"
        , "dom/mms/interfaces"
        , "dom/network/interfaces"
        , "dom/network/src"
        , "dom/permission"
        , "dom/plugins/base"
        , "dom/plugins/ipc"
        , "dom/power"
        , "dom/quota"
        , "dom/settings"
        , "dom/sms/interfaces"
        , "dom/sms/src"
        , "dom/src/events"
        , "dom/src/geolocation"
        , "dom/src/json"
        , "dom/src/jsurl"
        , "dom/src/notification"
        , "dom/src/offline"
        , "dom/src/storage"
        , "dom/system"
        , "dom/system/unix"
        , "dom/time"
        , "dom/workers"
        , "editor/composer/public"
        , "editor/composer/src"
        , "editor/idl"
        , "editor/libeditor/base"
        , "editor/libeditor/html"
        , "editor/libeditor/text"
        , "editor/txmgr/idl"
        , "editor/txmgr/src"
        , "editor/txtsvc/public"
        , "editor/txtsvc/src"
        , "embedding/base"
        , "embedding/browser/build"
        , "embedding/browser/webBrowser"
        , "embedding/components/appstartup/src"
        , "embedding/components/build"
        , "embedding/components/commandhandler/public"
        , "embedding/components/commandhandler/src"
        , "embedding/components/find/public"
        , "embedding/components/find/src"
        , "embedding/components/printingui/src/unixshared"
        , "embedding/components/webbrowserpersist/public"
        , "embedding/components/webbrowserpersist/src"
        , "embedding/components/windowwatcher/public"
        , "embedding/components/windowwatcher/src"
        , "extensions/auth"
        , "extensions/cookie"
        , "extensions/gio"
        , "extensions/permissions"
        , "extensions/pref/autoconfig/public"
        , "extensions/pref/autoconfig/src"
        , "extensions/spellcheck/hunspell/src"
        , "extensions/spellcheck/idl"
        , "extensions/spellcheck/src"
        , "extensions/universalchardet/src/base"
        , "extensions/universalchardet/src/xpcom"
        , "gfx/2d"
        , "gfx/angle"
        , "gfx/cairo/cairo/src"
        , "gfx/cairo/libpixman/src"
        , "gfx/gl"
        , "gfx/graphite2/src"
        , "gfx/harfbuzz/src"
        , "gfx/ipc"
        , "gfx/layers"
        , "gfx/ots/src"
        , "gfx/qcms"
        , "gfx/skia"
        , "gfx/src"
        , "gfx/thebes"
        , "gfx/ycbcr"
        , "hal"
        , "image/build"
        , "image/decoders"
        , "image/decoders/icon"
        , "image/decoders/icon/gtk"
        , "image/encoders/bmp"
        , "image/encoders/ico"
        , "image/encoders/jpeg"
        , "image/encoders/png"
        , "image/public"
        , "image/src"
        , "intl/build"
        , "intl/chardet/src"
        , "intl/hyphenation/src"
        , "intl/locale/idl"
        , "intl/locale/src"
        , "intl/locale/src/unix"
        , "intl/lwbrk/idl"
        , "intl/lwbrk/src"
        , "intl/strres/public"
        , "intl/strres/src"
        , "intl/uconv/idl"
        , "intl/uconv/src"
        , "intl/uconv/ucvcn"
        , "intl/uconv/ucvibm"
        , "intl/uconv/ucvja"
        , "intl/uconv/ucvko"
        , "intl/uconv/ucvlatin"
        , "intl/uconv/ucvtw"
        , "intl/uconv/ucvtw2"
        , "intl/uconv/util"
        , "intl/unicharutil/idl"
        , "intl/unicharutil/src"
        , "intl/unicharutil/util"
        , "intl/unicharutil/util/internal"
        , "ipc/app"
        , "ipc/chromium"
        , "ipc/glue"
        , "ipc/ipdl"
        , "ipc/testshell"
        , "ipc/unixsocket"
        , "js/ductwork/debugger"
        , "js/ipc"
        , "js/jsd"
        , "js/jsd/idl"
        #, "js/src"
        , "js/src/editline"
        #, "js/src/shell"
        , "js/xpconnect/idl"
        , "js/xpconnect/loader"
        , "js/xpconnect/shell"
        , "js/xpconnect/src"
        , "js/xpconnect/wrappers"
        , "layout/base"
        , "layout/build"
        , "layout/forms"
        , "layout/generic"
        , "layout/inspector/public"
        , "layout/inspector/src"
        , "layout/ipc"
        , "layout/mathml"
        , "layout/media"
        , "layout/printing"
        , "layout/style"
        , "layout/svg"
        , "layout/tables"
        , "layout/xul/base/public"
        , "layout/xul/base/src"
        , "layout/xul/base/src/grid"
        , "layout/xul/base/src/tree/public"
        , "layout/xul/base/src/tree/src"
        , "media/libcubeb/src"
        , "media/libjpeg"
        , "media/libnestegg/src"
        , "media/libogg/src"
        , "media/libopus"
        , "media/libpng"
        , "media/libsoundtouch/src"
        , "media/libspeex_resampler/src"
        , "media/libsydneyaudio/src"
        , "media/libtheora/lib"
        , "media/libvorbis/lib"
        , "media/libvpx"
        , "media/mtransport/build"
        , "media/mtransport/standalone"
        , "media/mtransport/third_party/nICEr/nicer_nicer"
        , "media/mtransport/third_party/nrappkit/nrappkit_nrappkit"
        , "media/webrtc/signaling/signaling_ecc"
        , "media/webrtc/signaling/signaling_sipcc"
        , "media/webrtc/signalingtest/signaling_ecc"
        , "media/webrtc/signalingtest/signaling_sipcc"
        , "media/webrtc/trunk/src/common_audio/common_audio_resampler"
        , "media/webrtc/trunk/src/common_audio/common_audio_signal_processing"
        , "media/webrtc/trunk/src/common_audio/common_audio_vad"
        , "media/webrtc/trunk/src/common_video/common_video_webrtc_jpeg"
        , "media/webrtc/trunk/src/common_video/common_video_webrtc_libyuv"
        , "media/webrtc/trunk/src/modules/modules_aec"
        , "media/webrtc/trunk/src/modules/modules_aecm"
        , "media/webrtc/trunk/src/modules/modules_aec_sse2"
        , "media/webrtc/trunk/src/modules/modules_agc"
        , "media/webrtc/trunk/src/modules/modules_apm_util"
        , "media/webrtc/trunk/src/modules/modules_audio_coding_module"
        , "media/webrtc/trunk/src/modules/modules_audio_conference_mixer"
        , "media/webrtc/trunk/src/modules/modules_audio_device"
        , "media/webrtc/trunk/src/modules/modules_audio_processing"
        , "media/webrtc/trunk/src/modules/modules_bitrate_controller"
        , "media/webrtc/trunk/src/modules/modules_CNG"
        , "media/webrtc/trunk/src/modules/modules_G711"
        , "media/webrtc/trunk/src/modules/modules_media_file"
        , "media/webrtc/trunk/src/modules/modules_NetEq"
        , "media/webrtc/trunk/src/modules/modules_ns"
        , "media/webrtc/trunk/src/modules/modules_opus"
        , "media/webrtc/trunk/src/modules/modules_PCM16B"
        , "media/webrtc/trunk/src/modules/modules_remote_bitrate_estimator"
        , "media/webrtc/trunk/src/modules/modules_rtp_rtcp"
        , "media/webrtc/trunk/src/modules/modules_udp_transport"
        , "media/webrtc/trunk/src/modules/modules_video_capture_module"
        , "media/webrtc/trunk/src/modules/modules_video_processing"
        , "media/webrtc/trunk/src/modules/modules_video_processing_sse2"
        , "media/webrtc/trunk/src/modules/modules_video_render_module"
        , "media/webrtc/trunk/src/modules/modules_webrtc_i420"
        , "media/webrtc/trunk/src/modules/modules_webrtc_utility"
        , "media/webrtc/trunk/src/modules/modules_webrtc_video_coding"
        , "media/webrtc/trunk/src/modules/video_coding/codecs/vp8/vp8_webrtc_vp8"
        , "media/webrtc/trunk/src/system_wrappers/source/system_wrappers_system_wrappers"
        , "media/webrtc/trunk/src/video_engine/video_engine_video_engine_core"
        , "media/webrtc/trunk/src/voice_engine/voice_engine_voice_engine_core"
        , "media/webrtc/trunk/testing/gtest_gtest"
        , "media/webrtc/trunk/testing/gtest_gtest_main"
        , "media/webrtc/trunk/third_party/libyuv/libyuv_libyuv"
        , "memory/build"
        , "memory/mozalloc"
        , "memory/mozjemalloc"
        , "mfbt"
        , "modules/libbz2/src"
        , "modules/libjar"
        , "modules/libjar/zipwriter/public"
        , "modules/libjar/zipwriter/src"
        , "modules/libmar/src"
        , "modules/libpref/public"
        , "modules/libpref/src"
        , "modules/zlib/src"
        , "mozglue/build"
        , "netwerk/base/public"
        , "netwerk/base/src"
        , "netwerk/build"
        , "netwerk/cache"
        , "netwerk/cookie"
        , "netwerk/dash/mpd"
        , "netwerk/dns"
        , "netwerk/ipc"
        , "netwerk/mime"
        , "netwerk/protocol/about"
        , "netwerk/protocol/data"
        , "netwerk/protocol/device"
        , "netwerk/protocol/file"
        , "netwerk/protocol/ftp"
        , "netwerk/protocol/http"
        , "netwerk/protocol/res"
        , "netwerk/protocol/viewsource"
        , "netwerk/protocol/websocket"
        , "netwerk/protocol/wyciwyg"
        , "netwerk/sctp/datachannel"
        , "netwerk/sctp/src"
        , "netwerk/socket"
        , "netwerk/srtp/src"
        , "netwerk/streamconv/converters"
        , "netwerk/streamconv/public"
        , "netwerk/streamconv/src"
        , "netwerk/wifi"
        , "other-licenses/snappy"
        , "parser/expat/lib"
        , "parser/html"
        , "parser/htmlparser/public"
        , "parser/htmlparser/src"
        , "parser/xml/public"
        , "parser/xml/src"
        , "profile/dirserviceprovider/src"
        , "profile/dirserviceprovider/standalone"
        , "profile/public"
        , "rdf/base/idl"
        , "rdf/base/src"
        , "rdf/build"
        , "rdf/datasource/src"
        , "rdf/util/src"
        , "rdf/util/src/internal"
        , "security/manager/boot/public"
        , "security/manager/boot/src"
        , "security/manager/pki/public"
        , "security/manager/pki/src"
        , "security/manager/ssl/public"
        , "security/manager/ssl/src"
        , "services/crypto/component"
        , "startupcache"
        , "storage/build"
        , "storage/public"
        , "storage/src"
        , "toolkit/components/alerts"
        , "toolkit/components/autocomplete"
        , "toolkit/components/build"
        , "toolkit/components/commandlines"
        , "toolkit/components/ctypes"
        , "toolkit/components/downloads"
        , "toolkit/components/exthelper"
        , "toolkit/components/feeds"
        , "toolkit/components/filepicker"
        , "toolkit/components/find"
        , "toolkit/components/intl"
        , "toolkit/components/mediasniffer"
        , "toolkit/components/osfile"
        , "toolkit/components/parentalcontrols"
        , "toolkit/components/passwordmgr"
        , "toolkit/components/perf"
        , "toolkit/components/places"
        , "toolkit/components/protobuf"
        , "toolkit/components/reflect"
        , "toolkit/components/remote"
        , "toolkit/components/satchel"
        , "toolkit/components/startup"
        , "toolkit/components/startup/public"
        , "toolkit/components/statusfilter"
        , "toolkit/components/telemetry"
        , "toolkit/components/typeaheadfind"
        , "toolkit/components/url-classifier"
        , "toolkit/components/urlformatter"
        , "toolkit/crashreporter"
        , "toolkit/crashreporter/client"
        , "toolkit/crashreporter/google-breakpad/src/client"
        , "toolkit/crashreporter/google-breakpad/src/client/linux/crash_generation"
        , "toolkit/crashreporter/google-breakpad/src/client/linux/handler"
        , "toolkit/crashreporter/google-breakpad/src/client/linux/minidump_writer"
        , "toolkit/crashreporter/google-breakpad/src/common"
        , "toolkit/crashreporter/google-breakpad/src/common/linux"
        , "toolkit/devtools/debugger"
        , "toolkit/identity"
        , "toolkit/library"
        , "toolkit/mozapps/extensions"
        , "toolkit/mozapps/update"
        , "toolkit/mozapps/update/common"
        , "toolkit/mozapps/update/updater"
        , "toolkit/profile"
        , "toolkit/system/dbus"
        , "toolkit/system/gnome"
        , "toolkit/system/unixproxy"
        , "toolkit/xre"
        , "tools/profiler"
        , "uriloader/base"
        , "uriloader/exthandler"
        , "uriloader/prefetch"
        , "view/src"
        , "webapprt/gtk2"
        ##, "widget"
        , "widget/gtk2"
        , "widget/gtkxtbin"
        , "widget/shared"
        , "widget/shared/x11"
        , "widget/xpwidgets"
        , "widget/xremoteclient"
        , "xpcom/base"
        , "xpcom/build"
        , "xpcom/components"
        , "xpcom/ds"
        , "xpcom/glue"
        , "xpcom/glue/nomozalloc"
        , "xpcom/glue/standalone"
        , "xpcom/idl-parser"
        , "xpcom/io"
        , "xpcom/reflect/xptcall/src"
        , "xpcom/reflect/xptcall/src/md/unix"
        , "xpcom/reflect/xptinfo/public"
        , "xpcom/reflect/xptinfo/src"
        , "xpcom/string/src"
        , "xpcom/stub"
        , "xpcom/system"
        , "xpcom/threads"
        , "xpcom/typelib/xpt/src"
        , "xpfe/appshell/public"
        , "xpfe/appshell/src"
        , "xpfe/components/build"
        , "xpfe/components/directory"
        , "xpfe/components/windowds"
	## FIREFOX TESTED other required dirs
        , "/netwerk/base/src", "/netwerk/cookie", "/netwerk/base", "/netwerk/dns"
        , "/netwerk/socket", "/netwerk/mime", "/netwerk/streamconv/src", "/netwerk/streamconv/converters"
        , "/netwerk/cache", "/netwerk/protocol/about", "/netwerk/protocol/data", "/netwerk/protocol/device"
        , "/netwerk/protocol/file", "/netwerk/protocol/ftp", "/netwerk/protocol/http", "/netwerk/protocol/res"
        , "/netwerk/protocol/viewsource", "/netwerk/protocol/websocket", "/netwerk/protocol/wyciwyg"
	, "/netwerk/ipc", "/netwerk/wifi", "/netwerk/build", "/extensions/auth", "/media/libjpeg"
        , "/modules/libbz2/src", "/gfx/qcms", "/ipc/chromium", "/ipc/glue", "/ipc/ipdl", "/ipc/testshell"
        , "/js/ipc", "/hal", "/js/xpconnect/wrappers", "/js/xpconnect/loader", "/js/xpconnect/src","/widget/gtkxtbin"
	, "/modules/libjar", "/storage/src", "/storage/build", "/extensions/cookie", "/extensions/permissions"
	, "/rdf/base/src", "/rdf/datasource/src", "/rdf/build", "/js/jsd", "/media/libvorbis/lib"
	, "/media/libopus", "/media/libnestegg/src", "/media/libvpx", "/media/libogg/src", "/media/libtheora/lib"
	, "/media/libsydneyaudio/src", "/media/webrtc/trunk/src/system_wrappers/source/system_wrappers_system_wrappers"
	, "/media/webrtc/trunk/third_party/libyuv/libyuv_libyuv"
	, "/media/webrtc/trunk/src/common_audio/common_audio_vad"
	, "/media/webrtc/trunk/src/common_audio/common_audio_signal_processing"
        , "/media/webrtc/trunk/src/common_audio/common_audio_resampler"
	, "/media/webrtc/trunk/src/common_video/common_video_webrtc_jpeg"
	, "/media/webrtc/trunk/src/common_video/common_video_webrtc_libyuv"
	, "/media/webrtc/trunk/src/voice_engine/voice_engine_voice_engine_core"
	, "/media/webrtc/trunk/src/video_engine/video_engine_video_engine_core"
	, "/media/webrtc/trunk/src/modules/modules_iLBC"
	, "/media/webrtc/trunk/testing/gtest_gtest_main"
	, "/media/webrtc/trunk/testing/gtest_gtest"
	, "/media/libspeex_resampler/src"
	, "/media/libcubeb/src"
	, "/media/libpng"
	, "/uriloader/base"
	, "/uriloader/exthandler"
	, "/uriloader/prefetch"
	, "/caps/src"
	, "/parser/expat/lib"
	, "/parser/xml/src"
	, "/parser/htmlparser/src"
	, "/parser/html"
	, "/gfx/cairo/cairo/src"
	, "/gfx/cairo/libpixman/src"
	, "/gfx/graphite2/src"
	, "/gfx/2d"
	, "/gfx/ycbcr"
	, "/gfx/angle"
	, "/gfx/src"
	, "/gfx/gl"
	, "/gfx/layers"
	, "/gfx/harfbuzz/src"
	, "/gfx/ots/src"
	, "/gfx/thebes"
	, "/gfx/ipc"
	, "/gfx/skia"
	, "/image/src"
	, "/image/decoders"
	, "/image/encoders/ico"
	, "/image/encoders/png"
	, "/image/encoders/jpeg"
	, "/image/encoders/bmp"
	, "/image/build"
	, "/dom/base"
	, "/dom/activities/src"
	, "/dom/bindings"
	, "/dom/battery"
	, "/dom/browser-element"
	, "/dom/alarm"
	, "/dom/devicestorage"
	, "/dom/file"
	, "/dom/media"
	, "/dom/power"
	, "/dom/sms/src"
	, "/dom/src/jsurl"
	, "/content/xtf/src"
	, "/accessible/src/xforms"
	, "/security/dbm/src"
	, "/security/nss/lib/util"
	, "/security/manager/"
	, "/media/webrtc/trunk/src/modules/modules_iSAC"
	, "/media/webrtc/trunk/src/modules/modules_iSACFix"
	, "/media/webrtc/trunk/src/modules/modules_webrtc_vp8"
	, "/media/webrtc/trunk/src/modules/modules_G722"
	, "/nsprpub/lib/ds"
	, "/nsprpub/lib/libc/src"
	, "/security/nss/lib/freebl"
	, "/security/nss/lib/softoken"
	, "/security/nss/lib/base"
	, "/security/nss/lib/dev"
	, "/security/nss/lib/pki"
	, "/security/nss/lib/libpkix/pkix/certsel"
	, "/security/nss/lib/libpkix/pkix/crlsel"
	, "/security/nss/lib/" ## UGH
	, "/security/nss/cmd/lib"
	, "/security/nss/cmd/shlibsign" ## actually its an output file problem
        ]

    for var in varList:
        #Final compile must be ordered specifically

        #-Qunused-arguments caused problems and is therefore ...unused...
	if var == '-Qunused-arguments':
            continue


	compilerFlags += [var]

        
        if isOutput:
            if var[-2:] == '.o':
                #FIREFOX
                #Objects explicitly needed
                for item in buildObjList:
                    if item in var:
                        doBuildObj = True
                for item in buildDirs:
                    if item in os.getcwd():
                        doBuildObj = True

                objFile = var
                rawFile = var[:-2]
            elif var[-3:] == '.so':
                #FIREFOX
                #Objects explicitly needed
                for item in buildFromObjList:
                    if ( item in var):
                        doBuildObj = True
                        doBuildBlob = False
                for item in buildDirs:
                    if item in os.getcwd():
                        doBuildObj = True
                        doBuildBlob = False
                binFile = var
                rawFile = var[:-3]
            else:
                #FIREFOX
                #Bin explicitly needed
                for item in buildFromObjList:
                    if ( item in var):
                        doBuildObj = True
                        doBuildBlob = False
                for item in buildDirs:
                    if item in os.getcwd():
                        doBuildObj = True
                        doBuildBlob = False
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
