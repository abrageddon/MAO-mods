/*===--- MultiCompilerOptions.cpp - Multicompiler Options -----
*
*
*  This file implements the Multi Compiler Options interface.
*
*  Author: kmanivan
*  Date: Dec 17, 2010
*
*===----------------------------------------------------------------------===*/

#include <iostream>
#include <fstream>
#include <string>

#include "MultiCompilerOptions.h"

namespace multicompiler {

bool ShuffleStackFrames;
unsigned int MaxStackFramePadding;
std::string MultiCompilerSeed;
int PreRARandomizerRange;
std::string RNGStateFile;
unsigned int NOPInsertionPercentage;
unsigned int MaxNOPsPerInstruction;
unsigned int MOVToLEAPercentage;
unsigned int EquivSubstPercentage;
unsigned int RandomizeFunctionList;
unsigned int FunctionAlignment;
bool RandomizeRegisters;
unsigned int ISchedRandPercentage;
unsigned int ProfiledNOPInsertion;
unsigned int NOPInsertionRange;
bool NOPInsertionUseLog;
unsigned int ProfiledNOPMinThreshold;
bool UseFunctionOptions;
std::string FunctionOptionsFile;


}
