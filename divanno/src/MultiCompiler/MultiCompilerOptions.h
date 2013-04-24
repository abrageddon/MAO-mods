/*===--- MultiCompilerOptions.h - Multicompiler Options -----
*
*
*  This file defines the Multi Compiler Options interface.
*
*===----------------------------------------------------------------------===*/

#ifndef MULTI_COMPILER_OPTIONS_H
#define MULTI_COMPILER_OPTIONS_H
#include <stdio.h>
#include <stdint.h>
#include <string>
#include <map>


namespace multicompiler {

extern bool ShuffleStackFrames;
extern unsigned int MaxStackFramePadding;
extern std::string MultiCompilerSeed;
extern int PreRARandomizerRange;
extern std::string RNGStateFile;
extern unsigned int NOPInsertionPercentage;
extern unsigned int MaxNOPsPerInstruction;
extern unsigned int MOVToLEAPercentage;
extern unsigned int EquivSubstPercentage;
extern unsigned int RandomizeFunctionList;
extern unsigned int FunctionAlignment;
extern bool RandomizeRegisters;
extern unsigned int ISchedRandPercentage;
extern unsigned int ProfiledNOPInsertion;
extern unsigned int NOPInsertionRange;
extern bool NOPInsertionUseLog;
extern unsigned int ProfiledNOPMinThreshold;
extern bool UseFunctionOptions;
extern std::string FunctionOptionsFile;

static const int NOPInsertionUnknown = -1;

}

#endif
