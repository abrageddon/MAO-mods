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

#include <llvm/ADT/SmallVector.h>
#include "llvm/MultiCompiler/MultiCompilerOptions.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/Regex.h"

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

#ifndef MAO_MULTI_COMPILER
static llvm::cl::opt<bool, true>
ShuffleStackFramesOpt("shuffle-stack-frames",
                     llvm::cl::desc("Shuffle variables in function stack frames"),
                     llvm::cl::location(ShuffleStackFrames),
                     llvm::cl::init(false));

static llvm::cl::opt<unsigned int, true>
MaxStackFramePaddingOpt("max-stack-pad-size",
                        llvm::cl::desc("Maximum amount of stack frame padding"),
                        llvm::cl::location(MaxStackFramePadding),
                        llvm::cl::init(0));

static llvm::cl::opt<std::string, true>
MultiCompilerOptionsOpt("multicompiler-seed",
                        llvm::cl::desc("RNG seed for multicompiler"),
                        llvm::cl::location(MultiCompilerSeed),
                        llvm::cl::init(""));

static llvm::cl::opt<int, true>
PreRARandomizerRangeOpt("pre-RA-randomizer-range",
                        llvm::cl::desc("Pre-RA instruction randomizer probability range; -1 for shuffle"),
                        llvm::cl::location(PreRARandomizerRange),
                        llvm::cl::init(0));

static llvm::cl::opt<unsigned int, true>
NOPInsertionPercentageOpt("nop-insertion-percentage",
                          llvm::cl::desc("Percentage of instructions that have NOPs prepended"),
                          llvm::cl::location(NOPInsertionPercentage),
                          llvm::cl::init(0));

static llvm::cl::opt<unsigned int, true>
MaxNOPsPerInstructionOpt("max-nops-per-instruction",
                          llvm::cl::desc("Maximum number of NOPs per instruction"),
                          llvm::cl::location(MaxNOPsPerInstruction),
                          llvm::cl::init(1));

static llvm::cl::opt<unsigned int, true>
MOVToLEAPercentageOpt("mov-to-lea-percentage",
                      llvm::cl::desc("Percentage of MOVs that get changed to LEA"),
                      llvm::cl::location(MOVToLEAPercentage),
                      llvm::cl::init(0));

static llvm::cl::opt<unsigned int, true>
EquivSubstPercentageOpt("equiv-subst-percentage",
                      llvm::cl::desc("Percentage of instructions which get equivalent-substituted"),
                      llvm::cl::location(EquivSubstPercentage),
                      llvm::cl::init(0));

static llvm::cl::opt<std::string, true>
RNGStateFileOpt("rng-state-file",
                llvm::cl::desc("Location of the rng state file"),
                llvm::cl::location(RNGStateFile),
                llvm::cl::init(std::string("")));

static llvm::cl::opt<unsigned int, true>
RandomizeFunctionListOpt("randomize-function-list",
                       llvm::cl::desc("Permute the function list"),
                       llvm::cl::location(RandomizeFunctionList),
                       llvm::cl::init(0));

static llvm::cl::opt<unsigned int, true>
FunctionAlignmentOpt("align-functions",
                     llvm::cl::desc("Specify alignment of functions as log2(align)"),
                     llvm::cl::location(FunctionAlignment),
                     llvm::cl::init(4));
 
static llvm::cl::opt<bool, true>
RandomizeRegistersOpt("randomize-registers",
                      llvm::cl::desc("Randomize the order of registers in allocation"),
                      llvm::cl::location(RandomizeRegisters),
                      llvm::cl::init(false));

static llvm::cl::opt<unsigned int, true>
ISchedRandPercentageOpt("isched-rand-percentage",
                        llvm::cl::desc("Percentage of instructions where schedule is randomized"),
                        llvm::cl::location(ISchedRandPercentage),
                        llvm::cl::init(0));

static llvm::cl::opt<unsigned int, true>
ProfiledNOPInsertionOpt("profiled-nop-insertion",
                        llvm::cl::desc("Use profile information in NOP insertion"),
                        llvm::cl::location(ProfiledNOPInsertion),
                        llvm::cl::init(0));

static llvm::cl::opt<unsigned int, true>
NOPInsertionRangeOpt("nop-insertion-range",
                      llvm::cl::desc("Range of values for NOP insertion percentage"),
                      llvm::cl::location(NOPInsertionRange),
                      llvm::cl::init(0));

static llvm::cl::opt<bool, true>
NOPInsertionUseLogOpt("nop-insertion-use-log",
                      llvm::cl::desc("Use a logarithm for NOP insertion"),
                      llvm::cl::location(NOPInsertionUseLog),
                      llvm::cl::init(false));

static llvm::cl::opt<unsigned int, true>
ProfiledNOPMinThresholdOpt("profiled-nop-min-threshold",
                           llvm::cl::desc("Threshold percentage of execution count"
                                          " for minimal NOP insertion"),
                           llvm::cl::location(ProfiledNOPMinThreshold),
                           llvm::cl::init(0));

static llvm::cl::opt<bool, true>
UseFunctionOptionsOpt("use-function-options",
                      llvm::cl::desc("Use per-function options"),
                      llvm::cl::location(UseFunctionOptions),
                      llvm::cl::init(false));

static llvm::cl::opt<std::string, true>
FunctionOptionsFileOpt("function-options-file",
                       llvm::cl::desc("File to read per-function options from"),
                       llvm::cl::location(FunctionOptionsFile),
                       llvm::cl::init("function-options.txt"));

#define OPT(x)   { &x, &x##Opt }

FunctionOptionInfo FunctionOptions[] = {
  OPT(ShuffleStackFrames),
  OPT(MaxStackFramePadding),
  OPT(NOPInsertionPercentage),
  OPT(MaxNOPsPerInstruction),
  OPT(MOVToLEAPercentage),
  OPT(EquivSubstPercentage),
  OPT(NOPInsertionRange),
  OPT(NOPInsertionUseLog),
  OPT(ProfiledNOPMinThreshold),
  // Must end in NULL, for proper iteration
  {NULL, NULL}
};


// FIXME: read&store this with a LLVM Pass
static FunctionOptionMap *funcOptMap = NULL;

static void readFunctionOptions() {
  if (funcOptMap != NULL)
    return;

  assert(UseFunctionOptions && "Trying to read function options when disabled");
  funcOptMap = new FunctionOptionMap();
  std::ifstream file(FunctionOptionsFile.c_str());
  if (!file.is_open()) {
    llvm::errs() << "Error: couldn't open per-function options file\n";
    return;
  }

  llvm::Regex funcRE("([_a-zA-Z0-9]+)[ \\t\\n\\f\\r]*{");
  llvm::Regex optRE("([-a-zA-Z]+)=([0-9]+)");
  llvm::Regex endRE("}");
  std::string line;
  llvm::SmallVector<llvm::StringRef, 4> matches;
  while (!file.eof()) {
    getline(file, line);
    if (funcRE.match(line, &matches)) {
      std::string funcName = matches[1];
      for (;;) {
        if (file.eof()) {
          llvm::errs() << "Error: function options reached end of file\n";
          break;
        }
        getline(file, line);
        if (endRE.match(line)) {
          break;
        }
        if (optRE.match(line)) {
          // FIXME: regex doesn't work correctly
          size_t eqPos = line.find_first_of('=');
          std::string optName = line.substr(0, eqPos);
          std::string optVal  = line.substr(eqPos + 1, line.length() - eqPos - 1);
          FunctionOptionKey key = std::make_pair(funcName, optName);
          // FIXME: check if option is valid
          (*funcOptMap)[key] = optVal;
        }
        // Ignore everything else
      }
    }
  }
  file.close();
}

bool findFunctionOption(
    const FunctionOptionKey &Key,
    std::string *Val) {
  readFunctionOptions();
  FunctionOptionMap::const_iterator it = funcOptMap->find(Key);
  if (it == funcOptMap->end())
    return false;

  *Val = it->second;
  return true;
}

#endif //MAO_MULTI_COMPILER
}
